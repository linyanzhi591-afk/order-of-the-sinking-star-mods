/* 只在角色描边绘制时选择材质，不修改模型或材质缓存。 */
typedef unsigned long long U64;
typedef unsigned int U32;
typedef unsigned char U8;
extern U64 material_capacity, material_table;
extern void *iat_module, *iat_proc, *iat_pid, *iat_key;
struct Settings { U32 key; U32 enabled; U32 held; U32 lock; } settings = {80, 1, 0, 0};
typedef void *(*Module)(const unsigned short *);
typedef void *(*Proc)(void *, const char *);
typedef U32 (*Pid)(void);
typedef short (*Key)(int);
typedef void *(*Foreground)(void);
typedef U32 (*WindowPid)(void *, U32 *);
static Foreground foreground;
static WindowPid window_pid;

static int equal(const U8 *p, U64 n, const char *s) {
    U64 i = 0;
    while (s[i]) { if (i >= n || p[i] != (U8)s[i]) return 0; ++i; }
    return i == n;
}

static void *lookup(const char *s) {
    U64 count = material_capacity;
    U8 *table = (U8 *)material_table;
    if (!table || !count || count > 1048576 || (count & (count-1))) return 0;
    U32 hash = 0x1505;
    U64 n = 0;
    while (s[n]) { hash = (hash ^ (U8)s[n])*0x1b3; ++n; }
    if (hash < 2) hash |= 2;
    U64 index = hash & (count-1);
    for (U64 step = 1; step <= count; ++step) {
        U8 *entry = table + index*32;
        U32 h = *(U32 *)entry;
        if (!h) return 0;
        if (h == hash && equal(*(U8 **)(entry+16), *(U64 *)(entry+8), s)) {
            U8 *resource = *(U8 **)(entry+24);
            return resource && resource[32] ? resource : 0;
        }
        index = (index+step) & (count-1);
    }
    return 0;
}

static void poll_key(void) {
    if (__sync_lock_test_and_set(&settings.lock, 1)) return;
    if (!foreground || !window_pid) {
        static const unsigned short user32[] = {'u','s','e','r','3','2','.','d','l','l',0};
        void *module = ((Module)iat_module)(user32);
        if (module) {
            foreground = (Foreground)((Proc)iat_proc)(module, "GetForegroundWindow");
            window_pid = (WindowPid)((Proc)iat_proc)(module, "GetWindowThreadProcessId");
        }
    }
    U32 pid = 0;
    U32 down = 0;
    if (foreground && window_pid) {
        window_pid(foreground(), &pid);
        if (pid == ((Pid)iat_pid)())
            down = (((Key)iat_key)((int)settings.key) & 0x8000) != 0;
    }
    if (down && !settings.held) settings.enabled ^= 1;
    settings.held = down;
    __sync_lock_release(&settings.lock);
}

void *select_outline(U8 *mesh, void *current) {
    poll_key();
    if (settings.enabled || !mesh) return current;
    U64 n = *(U64 *)mesh;
    U8 *name = *(U8 **)(mesh+8);
    const char *custom = 0;
    int druid = 0;
    if (equal(name,n,"warrior")) custom="ch_warrior_outline";
    else if (equal(name,n,"thief") || equal(name,n,"thief_alt")) custom="ch_thief_outline";
    else if (equal(name,n,"wizard") || equal(name,n,"wizard_alt")) custom="ch_wizard_outline";
    else if (equal(name,n,"cleric") || equal(name,n,"cleric_alt")) custom="ch_cleric_outline";
    else if (equal(name,n,"bard")) custom="ch_bard_outline";
    else if (equal(name,n,"druid")) { custom="ch_druid_outline"; druid=1; }
    if (!custom || lookup(custom) != current) return current;
    void *original = lookup(druid ? "druid_outline" : "entity_outline");
    return original ? original : current;
}
