package com.lx04.codexauth;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import android.util.Log;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 悬浮窗授权服务 - 类似 Codex/Work Buddy 的屏幕弹出授权
 */
public class OverlayService extends Service {

    private TextView quotaView;
    private final java.util.concurrent.ScheduledExecutorService quotaWorker = java.util.concurrent.Executors.newSingleThreadScheduledExecutor();
    private XiaoAiSpeech speech;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final Set<String> handledIds = ConcurrentHashMap.newKeySet();
    private volatile long nextPollAfter;
    private Thread pollingThread;
    private boolean submitting;
    private WindowManager windowManager;
    private View floatingView;
    private AtomicBoolean isShowing = new AtomicBoolean(false);
    private volatile boolean isRunning = true;
    private String mode = "codex"; // codex or workbuddy

    // PC 授权服务地址（可在 App 内修改，见 Config）
    private String pcServerUrl = "";

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        pcServerUrl = Config.getAuthUrl(this);
        createNotificationChannel();
        startForeground(1, createNotification());
        setupWindowManager();
        setupQuotaDisplay();
        speech = new XiaoAiSpeech(this);
        startPolling();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.hasExtra("MODE")) {
            mode = intent.getStringExtra("MODE");
        }
        return START_STICKY;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                "codex_auth",
                "Codex 授权服务",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("AI 命令授权悬浮窗服务");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification createNotification() {
        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, "codex_auth");
        } else {
            builder = new Notification.Builder(this);
        }
        return builder
            .setContentTitle("Codex 授权服务")
            .setContentText("监听 AI 命令请求...")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build();
    }

    private void setupWindowManager() {
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
    }

    private void setupQuotaDisplay() {
        quotaView = new TextView(this);
        quotaView.setText("CODEX 额度同步中…");
        quotaView.setTextSize(10);
        quotaView.setTextColor(Color.rgb(0, 240, 255));
        quotaView.setBackgroundColor(Color.rgb(5, 8, 16));
        quotaView.setGravity(Gravity.CENTER);
        quotaView.setPadding(8, 4, 8, 4);
        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
            PixelFormat.TRANSLUCENT);
        p.gravity = Gravity.TOP;
        try { windowManager.addView(quotaView, p); }
        catch (RuntimeException e) { Log.w("OverlayService", "Quota overlay unavailable", e); }
        quotaWorker.scheduleWithFixedDelay(() -> {
            String value;
            try { value = CodexQuota.read(this); }
            catch (Exception e) { value = "CODEX 额度连接中断 · 请检查电脑端额度服务"; }
            final String text = value;
            mainHandler.post(() -> {
                if (!isRunning) return;
                if (quotaView != null) quotaView.setText(text);
                if (floatingView != null) ((TextView)floatingView.findViewById(R.id.quota_text)).setText(text);
            });
        }, 0, 15, java.util.concurrent.TimeUnit.SECONDS);
    }

    private void startPolling() {
        // 每 2 秒轮询一次待授权命令
        pollingThread = new Thread(() -> {
            while (isRunning) {
                try {
                    Thread.sleep(2000);
                    if (isRunning) checkPendingCommands();
                } catch (InterruptedException e) {
                    break;
                }
            }
        }, "authorization-poll");
        pollingThread.start();
    }

    private void checkPendingCommands() {
        if (!isRunning || SystemClock.elapsedRealtime() < nextPollAfter || isShowing.get()) return; // 已有弹窗显示

        HttpURLConnection conn = null;
        try {
            URL url = new URL(pcServerUrl + "/api/pending");
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(3000);

            if (conn.getResponseCode() == 200) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                reader.close();
                String response = sb.toString();
                org.json.JSONArray commands = new org.json.JSONArray(response);

                for (int i = 0; i < commands.length(); i++) {
                    JSONObject cmd = commands.getJSONObject(i);
                    if (!handledIds.contains(cmd.optString("id"))) {
                        showAuthorizationPopup(cmd);
                        break;
                    }
                }
            }
        } catch (Exception e) {
            // 连接失败，继续轮询
        } finally { if (conn != null) conn.disconnect(); }
    }

    private void showAuthorizationPopup(JSONObject cmd) {
        if (!isShowing.compareAndSet(false, true)) return;

        String command = cmd.optString("command", "未知命令");
        String description = cmd.optString("description", "无描述");
        String riskLevel = cmd.optString("risk_level", "medium");
        String cmdId = cmd.optString("id", "");

        runOnUiThread(() -> {
            if (!isRunning) { isShowing.set(false); return; }
            detachPopup();
            submitting = false;
            if (quotaView != null) quotaView.setVisibility(View.GONE);
            // 创建悬浮窗视图
            floatingView = LayoutInflater.from(this).inflate(R.layout.floating_auth, null);

            TextView quotaText = floatingView.findViewById(R.id.quota_text);
            if (quotaView != null) quotaText.setText(quotaView.getText());
            TextView cmdText = floatingView.findViewById(R.id.cmd_text);
            TextView descText = floatingView.findViewById(R.id.desc_text);
            TextView riskText = floatingView.findViewById(R.id.risk_text);
            Button btnYes = floatingView.findViewById(R.id.btn_yes);
            Button btnNo = floatingView.findViewById(R.id.btn_no);

            cmdText.setText("> " + command);
            descText.setText("// " + description);

            // 风险等级
            int riskColor;
            String riskLabel;
            switch (riskLevel) {
                case "high":
                    riskColor = Color.RED;
                    riskLabel = "高风险";
                    break;
                case "medium":
                    riskColor = Color.YELLOW;
                    riskLabel = "中风险";
                    break;
                default:
                    riskColor = Color.GREEN;
                    riskLabel = "低风险";
            }
            riskText.setText(riskLabel);
            riskText.setTextColor(riskColor);

            // Yes 按钮
            btnYes.setOnClickListener(v -> {
                submitDecision(cmdId, true);
            });

            // No 按钮
            btnNo.setOnClickListener(v -> {
                submitDecision(cmdId, false);
            });

            // 添加悬浮窗
            WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                    : WindowManager.LayoutParams.TYPE_PHONE,
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                    | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT
            );
            params.gravity = Gravity.CENTER;
            params.y = 0;

            try {
                windowManager.addView(floatingView, params);
                speech.speak("皇上，请审批今天的奏折。");
                Log.i("OverlayService", "Popup shown: " + cmdId);
            } catch (RuntimeException e) {
                Log.e("OverlayService", "Unable to show popup", e);
                detachPopup();
                isShowing.set(false);
            }
        });
    }

    private void submitDecision(String cmdId, boolean authorized) {
        if (submitting || floatingView == null || !isRunning) return;
        submitting = true;
        View view = floatingView;
        Button yes = view.findViewById(R.id.btn_yes);
        Button no = view.findViewById(R.id.btn_no);
        TextView description = view.findViewById(R.id.desc_text);
        yes.setEnabled(false);
        no.setEnabled(false);
        description.setText("正在提交审批结果…");
        new Thread(() -> {
            HttpURLConnection conn = null;
            boolean success = false;
            try {
                conn = (HttpURLConnection) new URL(pcServerUrl + "/api/auth").openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                JSONObject json = new JSONObject();
                json.put("id", cmdId);
                json.put("authorized", authorized);
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(json.toString().getBytes(StandardCharsets.UTF_8));
                }
                if (conn.getResponseCode() != 200) throw new java.io.IOException("HTTP " + conn.getResponseCode());
                StringBuilder body = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) body.append(line);
                }
                if (!"ok".equals(new JSONObject(body.toString()).optString("status")))
                    throw new java.io.IOException("Server did not accept decision");
                success = true;
                handledIds.add(cmdId);
            } catch (Exception e) {
                Log.w("OverlayService", "Decision submission failed: " + cmdId, e);
            } finally { if (conn != null) conn.disconnect(); }
            final boolean accepted = success;
            runOnUiThread(() -> {
                if (!isRunning || floatingView != view) return;
                submitting = false;
                if (!accepted) {
                    description.setText("提交失败，请检查电脑连接后重试；结果尚未确认");
                    yes.setEnabled(true);
                    no.setEnabled(true);
                    return;
                }
                TextView risk = view.findViewById(R.id.risk_text);
                risk.setText(authorized ? "已同意" : "已拒绝");
                risk.setTextColor(authorized ? Color.GREEN : Color.RED);
                description.setText("审批结果已送达，即将返回初始界面…");
                yes.setText(authorized ? "已同意" : "已处理");
                no.setText(authorized ? "已处理" : "已拒绝");
                speech.speak(authorized ? "奴才收到。" : "不要啊皇上。");
                nextPollAfter = SystemClock.elapsedRealtime() + 5000;
                // Keep polling paused until the result window has been dismissed.
                mainHandler.postDelayed(() -> {
                    if (!isRunning || floatingView != view) return;
                    detachPopup();
                    isShowing.set(false);
                    Intent home = new Intent(this, MainActivity.class);
                    home.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                    home.putExtra("AUTH_SERVICE_RUNNING", true);
                    home.putExtra("MODE", mode);
                    try { startActivity(home); }
                    catch (RuntimeException e) { Log.w("OverlayService", "Unable to open initial screen", e); }
                }, 2000);
                Log.i("OverlayService", "Decision accepted: " + cmdId + " authorized=" + authorized);
            });
        }, "authorization-submit").start();
    }

    private void detachPopup() {
        if (quotaView != null) quotaView.setVisibility(View.VISIBLE);
        if (floatingView != null && windowManager != null) {
            try { windowManager.removeView(floatingView); }
            catch (IllegalArgumentException e) { Log.w("OverlayService", "Popup already detached", e); }
            floatingView = null;
        }
    }

    private void removePopup() {
        runOnUiThread(() -> { detachPopup(); isShowing.set(false); });
    }

    private void runOnUiThread(Runnable action) {
        mainHandler.post(action);
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;
        if (pollingThread != null) pollingThread.interrupt();
        quotaWorker.shutdownNow();
        if (quotaView != null) {
            try { windowManager.removeView(quotaView); } catch (IllegalArgumentException ignored) { }
            quotaView = null;
        }
        mainHandler.removeCallbacksAndMessages(null);
        if (speech != null) speech.close();
        detachPopup();
        isShowing.set(false);
    }
}
