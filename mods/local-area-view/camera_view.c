/* 只在最终显示镜头上叠加俯视；下一帧开始前还原普通镜头供游戏计算。 */
#include <stdint.h>
#include <xmmintrin.h>

typedef struct { float x, y, z; } Vec;
typedef struct { float x, y, z, w; } Quat;
typedef struct {
    Vec position, previous;
    Quat rotation;
    float fov, near_z, far_z;
} Camera;
typedef struct {
    uintptr_t owner, level;
    int active, overlaid;
    Camera normal;
    Quat overhead;
    float distance, fov;
} View;
__attribute__((section(".data"))) volatile View view = {0};

static float root(float x) {
    return _mm_cvtss_f32(_mm_sqrt_ss(_mm_set_ss(x)));
}
static float tangent(float x) {
    float result;
    __asm__ volatile ("flds %1; fptan; fstp %%st(0); fstps %0"
                      : "=m"(result) : "m"(x) : "st");
    return result;
}
static Camera *camera(uint8_t *s) { return (Camera *)(s + 0x3d98); }
static uintptr_t level(uint8_t *s) {
    uintptr_t count = *(uintptr_t *)(s + 0xdd0);
    uintptr_t *array = *(uintptr_t **)(s + 0xdd8);
    return count && array ? array[0] : 0;
}
static Vec forward(Quat q) {
    Vec v = {1-2*(q.y*q.y+q.z*q.z), 2*(q.x*q.y+q.z*q.w), 2*(q.x*q.z-q.y*q.w)};
    return v;
}
static int valid(float x) { return x > -1000000 && x < 1000000; }
static void restore(uint8_t *s) {
    if (view.overlaid && view.owner == (uintptr_t)s) {
        *camera(s) = view.normal;
    }
    view.overlaid = 0;
}

extern void current_level(void *context, uint8_t *state, uint8_t **result);
int use_native(void *context, uint8_t *s) {
    if (!s || (s[0x7f60] & 1) || !*(uintptr_t *)(s + 0xdd0)) return 0;
    uint8_t *l = 0;
    /* 使用游戏自己的当前关卡查询，避免多关卡同时加载时误取列表第一项。 */
    current_level(context, s, &l);
    if (l && l[0x3a2] && !l[0x42e] && *(uintptr_t *)(s+0x7e28)) {
        if (view.owner == (uintptr_t)s) restore(s);
        view.active = 0;
        return 1;
    }
    return 0;
}

void frame_begin(uint8_t *s) {
    if (!s) return;
    /* 换场景后不访问旧 state；只恢复当前仍然存活的镜头。 */
    if (view.owner != (uintptr_t)s || view.level != level(s)) {
        view.active = 0;
        view.overlaid = 0;
        return;
    }
    restore(s);
}

void toggle_view(uint8_t *s) {
    if (!s || (s[0x7f60] & 1)) return;
    if (view.owner == (uintptr_t)s && view.active) {
        restore(s);
        view.active = 0;
        return;
    }
    restore(s);
    Camera c = *camera(s);
    Vec f = forward(c.rotation);
    float floor = *(float *)(s + 0x6828);
    float distance = (floor - c.position.z) / f.z;
    /* 镜头水平、向上或数据无效时不生成无穷远位置。 */
    if (!(f.z < -0.0001f && distance > 0.001f && distance < 1000000 &&
          c.fov > 0 && c.fov < 3.14f)) return;
    float rx = 2*(c.rotation.x*c.rotation.y-c.rotation.z*c.rotation.w);
    float ry = 1-2*(c.rotation.x*c.rotation.x+c.rotation.z*c.rotation.z);
    float length = root(rx*rx+ry*ry);
    if (!(length > 0.0001f)) return;
    rx /= length; ry /= length;
    if (ry > 1) ry = 1;
    if (ry < -1) ry = -1;
    float half_c = root((1+ry)*0.5f);
    float half_s = root((1-ry)*0.5f);
    if (rx > 0) half_s = -half_s;
    const float h = 0.7071067811865475f;
    Quat q = {-half_s*h, half_c*h, half_s*h, half_c*h};
    view.owner = (uintptr_t)s;
    view.level = level(s);
    view.overhead = q;
    /* 以 v0.1.5 的距离为基准，固定拉远 17%，不按整张地图适配。 */
    view.distance = distance*1.17f;
    view.fov = c.fov;
    view.active = 1;
    s[0x3dd4] = 0;
}

void frame_end(uint8_t *s) {
    if (!s || !view.active || view.owner != (uintptr_t)s) return;
    if (view.level != level(s) || s[0x3dd4] != 0) {
        view.active = 0;
        return;
    }
    Camera *c = camera(s);
    Vec f = forward(c->rotation);
    float floor = *(float *)(s + 0x6828);
    float distance = (floor-c->position.z)/f.z;
    if (!(f.z < -0.0001f && distance > 0.001f && distance < 1000000)) return;
    Vec focus = {c->position.x+f.x*distance, c->position.y+f.y*distance, floor};
    if (!valid(focus.x) || !valid(focus.y) || !valid(floor)) return;
    view.normal = *c;
    float fitted = view.distance;
    Quat q = view.overhead;
    /* 镜头沿屏幕上方向移动可视高度的 6%，使场景整体向下偏移 6%。 */
    float shift = fitted*tangent(view.fov*0.5f)*0.12f;
    float up_x = 2*(q.x*q.z+q.y*q.w);
    float up_y = 2*(q.y*q.z-q.x*q.w);
    c->position = (Vec){focus.x+up_x*shift, focus.y+up_y*shift, floor+fitted};
    if (fitted+10 > c->far_z) c->far_z = fitted+10;
    c->previous = c->position;
    c->rotation = view.overhead;
    c->fov = view.fov;
    view.overlaid = 1;
}
