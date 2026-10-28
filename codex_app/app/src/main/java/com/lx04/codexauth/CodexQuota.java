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
    static String read(android.content.Context context) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(Config.getQuotaUrl(context) + "/api/codex-usage").openConnection();

        conn.setConnectTimeout(3000); conn.setReadTimeout(3000);
        try {
            if (conn.getResponseCode() != 200) throw new java.io.IOException("Quota HTTP " + conn.getResponseCode());
            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line=reader.readLine()) != null) body.append(line);
            }
            JSONObject data = new JSONObject(body.toString());
            if (!data.optBoolean("available")) return "CODEX 额度暂不可用 · 等待电脑端使用记录";
            JSONArray windows=data.getJSONArray("windows");
            StringBuilder top=new StringBuilder("CODEX ");
            StringBuilder bottom=new StringBuilder();
            for (int i=0; i<windows.length(); i++) {
                JSONObject w=windows.getJSONObject(i);
                int mins=w.getInt("window_minutes");
                String label=mins==10080 ? "每周" : mins%60==0 ? (mins/60)+"小时" : mins+"分钟";
                if (i>0) { top.append("  |  "); bottom.append(" · "); }
                top.append(label).append("剩余 ");
                if (w.optBoolean("expired")) top.append("待更新");
                else top.append(String.format(Locale.CHINA,"%.0f%%",w.getDouble("remaining_percent")));
                bottom.append(label).append("重置 ").append(time(w.getLong("resets_at")));
            }
            return top + "\n" + bottom + "\n" +
                (data.optBoolean("stale") ? "旧记录，请在电脑端刷新额度 · " : "最近同步记录 · ") + time(data.getLong("updated_at"));
        } finally { conn.disconnect(); }
    }
}
