"""水面细网格：仅修改四类水面最终 RGB，保持原有 alpha 和深度。"""
import re



def inject(text, family):
    """保留原着色计算，在最终 RGB 混合网格；alpha 与深度写入保持原样。"""
    if family not in {'water_flow', 'water_ripple', 'water_simple', 'ocean'}:
        raise ValueError('仅支持四类水面着色器')
    # TEXCOORD0 是已有顶点程序传递的世界坐标。先严格检查签名。
    if not re.search(r'; TEXCOORD\s+0\s+xyz\s+1\s+NONE\s+float\s+xyz', text):
        raise ValueError('世界坐标签名不匹配')
    if '%sg_' in text:
        raise ValueError('拒绝重复注入')
    bind = re.search(r'(%\d+) = call %dx.types.Handle @dx.op.createHandleFromBinding[^\n]*'
                     r'%dx.types.ResBind \{ i32 3, i32 3, i32 0, i8 2 \}', text)
    if bind:
        handle = re.search(r'(%\d+) = call %dx.types.Handle @dx.op.annotateHandle\(i32 216, '
                           r'%dx.types.Handle '+re.escape(bind[1])+r',', text)
        if not handle:
            raise ValueError('缺少 cb3 类型标注')
    else:
        handle = re.search(r'(%\d+) = call %dx.types.Handle @dx.op.createHandle'
                           r'\(i32 57, i8 2, i32 \d+, i32 3, i1 false\)', text)
        if not handle:
            raise ValueError('缺少 cb3 参数绑定')
    if family == 'ocean':
        if not re.search(r'float shore_mask_spread;\s+; Offset:\s+276', text) or not re.search(r'float3 shore_mask_color;\s+; Offset:\s+288', text):
            raise ValueError('海面保留字段布局不匹配')
        prefix = f'''  %sg_cb = call %dx.types.CBufRet.f32 @dx.op.cbufferLoadLegacy.f32(i32 59, %dx.types.Handle {handle[1]}, i32 17)
  %sg_flag = extractvalue %dx.types.CBufRet.f32 %sg_cb, 2
  %sg_on = fcmp ogt float %sg_flag, 5.000000e-01
'''
    else:
        flag = re.search(r';\s+int material_flags;\s+; Offset:\s+(\d+)', text)
        if not flag or int(flag[1]) not in (0, 4):
            raise ValueError('缺少已验证的 material_flags 反射')
        column = int(flag[1])//4
        # 原材质计算读取的标志值先清除保留位；保存原有低位计算路径。
        loads = re.findall(r'(%\d+) = call %dx.types.CBufRet.i32 @dx.op.cbufferLoadLegacy.i32\(i32 59, %dx.types.Handle '+re.escape(handle[1])+r', i32 0\)', text)
        for load in loads:
            pattern = r'  (%\d+) = extractvalue %dx.types.CBufRet.i32 '+re.escape(load)+r', '+str(column)+r'(?=\n)'
            def clean(m):
                raw = '%sg_original'+m[1][1:]
                return '  '+raw+' = extractvalue %dx.types.CBufRet.i32 '+load+', '+str(column)+'\n  '+m[1]+' = and i32 '+raw+', 2147483647'
            text = re.sub(pattern, clean, text)
        prefix = f'''  %sg_cb = call %dx.types.CBufRet.i32 @dx.op.cbufferLoadLegacy.i32(i32 59, %dx.types.Handle {handle[1]}, i32 0)
      %sg_flag = extractvalue %dx.types.CBufRet.i32 %sg_cb, {column}
      %sg_bit = and i32 %sg_flag, -2147483648
      %sg_on = icmp ne i32 %sg_bit, 0
    '''
    # 参数绑定在入口定义，因此入口末尾计算导数，避免在非一致分支中求导。
    body = []
    for axis in (0, 1):
        a = f'sg_{axis}'
        body.append(f'''  %{a} = call float @dx.op.loadInput.f32(i32 4, i32 1, i32 0, i8 {axis}, i32 undef)
  %{a}_offset = fadd float %{a}, 5.000000e-01
  %{a}_frac = call float @dx.op.unary.f32(i32 22, float %{a}_offset)
  %{a}_reverse = fsub float 1.000000e+00, %{a}_frac
  %{a}_dist = call float @dx.op.binary.f32(i32 36, float %{a}_frac, float %{a}_reverse)
  %{a}_dx = call float @dx.op.unary.f32(i32 83, float %{a})
  %{a}_dy = call float @dx.op.unary.f32(i32 84, float %{a})
  %{a}_dx2 = fmul float %{a}_dx, %{a}_dx
  %{a}_dy2 = fmul float %{a}_dy, %{a}_dy
  %{a}_sum = fadd float %{a}_dx2, %{a}_dy2
  %{a}_grad0 = call float @dx.op.unary.f32(i32 24, float %{a}_sum)
  %{a}_grad = call float @dx.op.binary.f32(i32 35, float %{a}_grad0, float 0x3EB0C6F7A0000000)
  %{a}_pixels = fdiv float %{a}_dist, %{a}_grad
  %{a}_coverage0 = fsub float 1.500000e+00, %{a}_pixels
  %{a}_coverage = call float @dx.op.unary.f32(i32 7, float %{a}_coverage0)
''')
    body.append('''  %sg_union = call float @dx.op.binary.f32(i32 35, float %sg_0_coverage, float %sg_1_coverage)
  %sg_alpha0 = fmul float %sg_union, 0x3FEB333340000000
  %sg_alpha = select i1 %sg_on, float %sg_alpha0, float 0.000000e+00
''')
    insertion = prefix+''.join(body)
    # 在入口中求导，避免末尾可能含材质非一致分支。
    annotated_end = text.index('\n', handle.end())+1
    text = text[:annotated_end]+insertion+text[annotated_end:]
    outputs = re.findall(r'  call void @dx.op.storeOutput.f32\(i32 5, i32 0, i32 0, i8 ([012]), float ([^ )]+)\)', text)
    if len(outputs) != 3 or {x[0] for x in outputs} != {'0','1','2'}:
        raise ValueError('最终 RGB 输出不唯一')
    for channel, value in outputs:
        original = f'  call void @dx.op.storeOutput.f32(i32 5, i32 0, i32 0, i8 {channel}, float {value})'
        # 线性色值约对应 sRGB 22；这里的曝光适配仍需实机检验。
        replacement = f'''  %sg_delta{channel} = fsub float 0x3F80624DE0000000, {value}
  %sg_mix{channel} = fmul float %sg_delta{channel}, %sg_alpha
  %sg_rgb{channel} = fadd float {value}, %sg_mix{channel}
  call void @dx.op.storeOutput.f32(i32 5, i32 0, i32 0, i8 {channel}, float %sg_rgb{channel})'''
        text = text.replace(original, replacement)
    return text
