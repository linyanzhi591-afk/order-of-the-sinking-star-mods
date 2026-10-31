.intel_syntax noprefix
.text

.macro save_state pad
    pushfq
    push rax
    push rcx
    push rdx
    push r8
    push r9
    push r10
    push r11
    sub rsp, \pad
    movups [rsp+0x20], xmm0
    movups [rsp+0x30], xmm1
    movups [rsp+0x40], xmm2
    movups [rsp+0x50], xmm3
    movups [rsp+0x60], xmm4
    movups [rsp+0x70], xmm5
.endm
.macro restore_state pad
    movups xmm0, [rsp+0x20]
    movups xmm1, [rsp+0x30]
    movups xmm2, [rsp+0x40]
    movups xmm3, [rsp+0x50]
    movups xmm4, [rsp+0x60]
    movups xmm5, [rsp+0x70]
    add rsp, \pad
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdx
    pop rcx
    pop rax
    popfq
.endm

.global water_constants_hook
water_constants_hook:
    save_state 0x80
    call water_after_constants
    restore_state 0x80
    mov rcx, [rsi+8]
    mov rax, [rcx+0x290]
    jmp water_constants_return
