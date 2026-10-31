/* 水面网格显示：只识别四类水面，仅 O 键，启动关闭。 */
typedef unsigned long long U64;
typedef unsigned int U32;
typedef unsigned short U16;
typedef unsigned char U8;
extern void *iat_module, *iat_proc, *iat_pid, *iat_key;
extern U64 material_capacity;
extern U8 *material_table;
extern U8 render_context[];
extern void upload_buffer_view(U8 *, U8 *, U8 *, U8);
struct WaterState { U32 enabled, held, lock, ticks; } water_state = {0, 0, 0, 0};
typedef void *(*Module)(const U16 *);
typedef void *(*Proc)(void *, const char *);
typedef U32 (*Pid)(void);
typedef short (*Key)(int);
typedef void *(*Foreground)(void);
typedef U32 (*WindowPid)(void *, U32 *);
static Foreground foreground;
static WindowPid window_pid;

static void poll_key(void) {
    if (!foreground || !window_pid) {
        static const U16 user32[] = {'u','s','e','r','3','2','.','d','l','l',0};
        void *module = ((Module)iat_module)(user32);
        if (module) {
            foreground = (Foreground)((Proc)iat_proc)(module, "GetForegroundWindow");
            window_pid = (WindowPid)((Proc)iat_proc)(module, "GetWindowThreadProcessId");
        }
    }
    U32 pid = 0;
    if (foreground && window_pid) window_pid(foreground(), &pid);
    if (!foreground || !window_pid || pid != ((Pid)iat_pid)()) {
        /* 失焦后必须先松开 O，避免回到游戏时误切换。 */
        water_state.held = 1;
        return;
    }
    U32 down = (((Key)iat_key)(79) & 0x8000) != 0;
    if (down && !water_state.held) water_state.enabled ^= 1;
    water_state.held = down;
}

/* 沿用已核验的游戏参数哈希布局；不添加或扩容常量缓冲区。 */
static U8 *descriptor(U8 *meta, U32 hash) {
    if ((U64)meta < 65536) return 0;
    U64 count = *(U64 *)(meta+0x30);
    U8 *table = *(U8 **)(meta+0x58), *descs = *(U8 **)(meta+8);
    if (!count || count > 65536 || (count & (count-1)) || !table || !descs) return 0;
    U64 mixed = (U64)(hash ^ 0x1505U)*0x9e3779b97f4a7c15ULL;
    U32 h = (U32)(mixed >> 32);
    if (!(mixed >> 33)) h |= 2;
    U32 index = h & (U32)(count-1);
    for (U32 step = 1; step <= count; ++step) {
        U8 *entry = table+index*12;
        U32 found = *(U32 *)entry;
        if (!found) return 0;
        if (found == h && *(U32 *)(entry+4) == hash) {
            U8 *d = descs+(*(U16 *)(entry+8))*12;
            U32 offset = *(U32 *)d;
            return d[8] == 255 && offset <= 65532 && !(offset & 3) ? d : 0;
        }
        index = (index+step) & (U32)(count-1);
    }
    return 0;
}
static int has(U8 *mapper, U32 hash, U32 offset) {
    U8 *d = descriptor(mapper, hash);
    return d && *(U32 *)d == offset && *(U16 *)(d+4) == 4;
}
static void update_water(void) {
    if (!*(U8 **)(render_context+0x80)) return;
    U64 count = material_capacity;
    U8 *table = material_table;
    if (!table || count > 262144) return;
    for (U64 i = 0; i < count; ++i) {
        U8 *entry = table+i*32;
        if (*(U32 *)entry < 2) continue;
        U8 *material = *(U8 **)(entry+24);
        if (!material) continue;
        U8 *data = *(U8 **)(material+64);
        if (!data || data[5]) continue;
        U8 *resource = *(U8 **)(data+24);
        if (!resource) continue;
        U8 *shader = *(U8 **)resource;
        if (!shader) continue;
        U8 *mapper = shader+0x3a0;
        U32 size = *(U32 *)(mapper+0x68), ocean = 0;
        if (size == 116 && has(mapper, 0xf58697ddU, 16)
            && descriptor(mapper, 0x3968fa1cU) && descriptor(mapper, 0xaa79d1d0U)) { }
        else if (size == 20 && has(mapper, 0x98fc2022U, 4)
            && descriptor(mapper, 0x7795f48cU) && descriptor(mapper, 0x8f7ae314U)) { }
        else if (size == 76 && has(mapper, 0xd65e3d04U, 72)
            && descriptor(mapper, 0xf3219f58U) && descriptor(mapper, 0x25c46620U)) { }
        else if (size == 504 && has(mapper, 0x20623f84U, 4)
            && has(mapper, 0xb62f5a17U, 208) && has(mapper, 0xe3d88b44U, 500)) ocean = 1;
        else continue;
        U32 offset = 280;
        if (!ocean) {
            U8 *flag = descriptor(mapper, 0xa9133cf4U);
            if (!flag || *(U16 *)(flag+4) != 4) continue;
            offset = *(U32 *)flag;
            if (offset != 0 && offset != 4) continue;
        }
        U64 constants = *(U64 *)mapper;
        U8 *descs = *(U8 **)(mapper+8);
        if (!descs || constants > 512) continue;
        U32 occupied = 0;
        for (U64 j = 0; j < constants; ++j) {
            U8 *d = descs+j*12;
            if (!ocean && d[8] == 31) occupied = 1;
            U32 at = *(U32 *)d, length = *(U16 *)(d+4);
            if (ocean && length && at < 284 && at+length > 280) occupied = 1;
        }
        if (occupied) continue;
        U64 slots = *(U64 *)(data+0x88);
        U8 *bindings = *(U8 **)(data+0xb0);
        if (!bindings || slots > 1024) continue;
        for (U64 j = 0; j < slots; ++j) {
            U8 *b = bindings+j*24;
            if (*(U32 *)b < 2) continue;
            U8 *binding = *(U8 **)(b+16);
            if (!binding || *(U64 *)binding != size) continue;
            U8 *values = *(U8 **)(binding+8);
            if (!values || !*(U8 **)(binding+0x18) || *(U32 *)(binding+0x2c) != size) continue;
            U32 old = *(U32 *)(values+offset);
            U32 value = ocean ? (water_state.enabled ? 0x3f800000U : 0) :
                ((old & 0x7fffffffU) | (water_state.enabled ? 0x80000000U : 0));
            if (old == value) continue;
            *(U32 *)(values+offset) = value;
            upload_buffer_view(render_context, binding+0x18, values, 1);
            binding[0x10] = 0;
        }
    }
}
void water_after_constants(void) {
    /* 覆盖查询和上传全程，上传重入或其他线程不并发改写材质。 */
    if (__sync_lock_test_and_set(&water_state.lock, 1)) return;
    U32 before = water_state.enabled;
    poll_key();
    if ((water_state.ticks++ & 1023) == 0 || before != water_state.enabled) update_water();
    __sync_lock_release(&water_state.lock);
}
