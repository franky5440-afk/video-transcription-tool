def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi+0.05)/(lo+0.05)

# 改完後把新色值填進來，全部組合要 >= 4.5
light = dict(bg="#eef2f8", card="#ffffff", text="#101828", text2="#55637d",
             accent="#0f766e", btn="#047857", btntext="#ffffff",
             success="#166534", sbg="#dcfce7", error="#b91c1c", ebg="#fee2e2",
             running="#0369a1", rbg="#e0f2fe",
             pending="#4b5c78", pbg="#e2e8f2", skipbg="#e2e8f2")
dark = dict(bg="#0b1220", card="#151e32", text="#f1f5f9", text2="#94a3b8",
            accent="#5eead4", btn="#059669", btntext="#04110c",
            success="#4ade80", sbg="#0d3321", error="#f87171", ebg="#3b1213",
            running="#38bdf8", rbg="#0c2a44",
            pending="#93a5c4", pbg="#1d2941", skipbg="#1c2740")

checks = [("主文字 on 卡片", "text", "card"), ("次要文字 on 卡片", "text2", "card"),
          ("次要文字 on 頁底", "text2", "bg"), ("連結 on 卡片", "accent", "card"),
          ("按鈕文字 on 按鈕", "btntext", "btn"),
          ("完成 on 完成底", "success", "sbg"), ("失敗 on 失敗底", "error", "ebg"),
          ("進行中 on 進行中底", "running", "rbg"),
          ("略過 on 略過底", "pending", "skipbg"),
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