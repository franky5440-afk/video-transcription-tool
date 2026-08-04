def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi+0.05)/(lo+0.05)

# 改完後把新色值填進來，7 組全部要 >= 4.5
light = dict(bg="#f5f5f7", card="#ffffff", text="#1d1d1f", text2="#6e6e73",
             accent="#0071e3", success="#176c2e", sbg="#e6f4ea",
             pending="#67676e", pbg="#ececec", skipbg="#efefef")
dark = dict(bg="#1c1c1e", card="#2c2c2e", text="#f5f5f7", text2="#a1a1a6",
            accent="#409cff", success="#4cd873", sbg="#113a1e",
            pending="#ababb1", pbg="#3a3a3c", skipbg="#333335")

checks = [("主文字 on 卡片", "text", "card"), ("次要文字 on 卡片", "text2", "card"),
          ("次要文字 on 頁底", "text2", "bg"), ("連結 on 卡片", "accent", "card"),
          ("完成 on 完成底", "success", "sbg"), ("略過 on 略過底", "pending", "skipbg"),
          ("待處理 on 待處理底", "pending", "pbg")]
fail = 0
for mode, t in (("淺色", light), ("深色", dark)):
    print(f"\n──── {mode} ────")
    for label, fg, bg in checks:
        r = ratio(t[fg], t[bg])
        ok = r >= 4.5
        fail += 0 if ok else 1
        print(f"{'✅' if ok else '🔴'} {label:<20} {t[fg]} on {t[bg]} = {r:.2f}:1")
print(f"\n{'✅ 全部通過' if not fail else f'🔴 {fail} 組未達 4.5:1'}")
raise SystemExit(1 if fail else 0)