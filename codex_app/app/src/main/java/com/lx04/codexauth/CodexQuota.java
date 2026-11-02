package com.lx04.codexauth;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

final class CodexQuota {
    private static String time(long seconds) {
        SimpleDateFormat format = new SimpleDateFormat("MM/dd HH:mm", Locale.CHINA);
        format.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));
        return format.format(new Date(seconds * 1000));
    }

    /**
     * 读取额度文本。根据 mode 请求不同端点：
     *  - codex      -> /api/codex-usage      (Codex CLI token_count 用量窗口)
     *  - workbuddy  -> /api/workbuddy-usage  (WorkBuddy 每日积分余额)
     */
    static String read(android.content.Context context, String mode) throws Exception {
        boolean workbuddy = "workbuddy".equalsIgnoreCase(mode);
        String brand = workbuddy ? "WORKBUDDY" : "CODEX";
        String endpoint = workbuddy ? "/api/workbuddy-usage" : "/api/codex-usage";

        HttpURLConnection conn = (HttpURLConnection) new URL(Config.getQuotaUrl(context) + endpoint).openConnection();
        conn.setConnectTimeout(3000); conn.setReadTimeout(3000);
        try {
            if (conn.getResponseCode() != 200) throw new java.io.IOException("Quota HTTP " + conn.getResponseCode());
            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line=reader.readLine()) != null) body.append(line);
            }
            JSONObject data = new JSONObject(body.toString());

            if (!data.optBoolean("available"))
                return brand + " 额度暂不可用 · 等待电脑端使用记录";

            if (workbuddy) {
                int total  = data.optInt("total", 0);
                int streak = data.optInt("streak", 0);
                boolean claimed = data.optBoolean("claimed_today", false);
                StringBuilder sb = new StringBuilder(brand + " 额度\n");
                sb.append("累计 ").append(total).append(" 积分 · 连续 ").append(streak).append(" 天");
                if (!claimed) sb.append(" · 今日未领");
                sb.append("\n").append(data.optBoolean("stale") ? "旧记录，请在电脑端领取额度 · " : "最近同步记录 · ")
                  .append(time(data.optLong("updated_at")));
                return sb.toString();
            }

            // codex: window-based usage
            JSONArray windows = data.getJSONArray("windows");
            StringBuilder top = new StringBuilder(brand + " ");
            StringBuilder bottom = new StringBuilder();
            for (int i = 0; i < windows.length(); i++) {
                JSONObject w = windows.getJSONObject(i);
                int mins = w.getInt("window_minutes");
                String label = mins == 10080 ? "每周" : mins % 60 == 0 ? (mins / 60) + "小时" : mins + "分钟";
                if (i > 0) { top.append("  |  "); bottom.append(" · "); }
                top.append(label).append("剩余 ");
                if (w.optBoolean("expired")) top.append("待更新");
                else top.append(String.format(Locale.CHINA, "%.0f%%", w.getDouble("remaining_percent")));
                bottom.append(label).append("重置 ").append(time(w.getLong("resets_at")));
            }
            return top + "\n" + bottom + "\n" +
                (data.optBoolean("stale") ? "旧记录，请在电脑端刷新额度 · " : "最近同步记录 · ") + time(data.getLong("updated_at"));
        } finally { conn.disconnect(); }
    }
}
