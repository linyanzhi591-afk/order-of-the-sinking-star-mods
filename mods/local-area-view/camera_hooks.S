.intel_syntax noprefix
.text
.global hook_toggle, hook_begin, hook_end
.extern game_state, return_begin, return_end, return_toggle

hook_toggle:
    push rcx
    sub rsp, 0x20
    mov rdx, QWORD PTR [rip + game_state]
    call use_native
    add rsp, 0x20
    pop rcx
    test eax, eax
    jnz native_toggle
    mov rcx, QWORD PTR [rip + game_state]
    jmp toggle_view
native_toggle:
    /* 原生支持的关卡完整返回原回调，保持原取景和缩放。 */
    push r15
    push r14
    push r12
    jmp return_toggle

/* 保留原调用点所有易失寄存器和标志；不改变调用者的栈参数。 */
.macro save
    pushfq
    push rax
    push rcx
    push rdx
    push r8
    push r9
    push r10
    push r11
    sub rsp, 0x80
    movups [rsp+0x20], xmm0
    movups [rsp+0x30], xmm1
    movups [rsp+0x40], xmm2
    movups [rsp+0x50], xmm3
    movups [rsp+0x60], xmm4
    movups [rsp+0x70], xmm5
.endm
.macro restore
    movups xmm0, [rsp+0x20]
    movups xmm1, [rsp+0x30]
    movups xmm2, [rsp+0x40]
    movups xmm3, [rsp+0x50]
    movups xmm4, [rsp+0x60]
    movups xmm5, [rsp+0x70]
    add rsp, 0x80
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdx
    pop rcx
    pop rax
    popfq
.endm
hook_begin:
    /* 原函数入口 RSP 为 8 mod 16。 */
    sub rsp, 8
    save
    mov rcx, QWORD PTR [rip+game_state]
    call frame_begin
    restore
    add rsp, 8
    push r15
    push r14
    push r13
    jmp return_begin
hook_end:
    /* 原函数内部 RSP 为 0 mod 16。 */
    save
    mov rcx, r13
    call frame_end
    restore
    mov r14, QWORD PTR [rsp+0x78]
    jmp return_end
