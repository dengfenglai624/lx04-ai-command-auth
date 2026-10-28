package com.lx04.codexauth;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Binder;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Parcel;
import android.os.RemoteException;
import android.util.Log;
import android.widget.Toast;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** LX04 firmware's exported, normal-permission device service. */
final class XiaoAiSpeech {
    private static final String TAG = "XiaoAiSpeech";
    private static final String DESCRIPTOR = "com.xiaomi.mico.device.service.iface.IMicoDeviceServiceInterface";
    private static final String CALLBACK = "com.xiaomi.mico.device.service.iface.IUbusRelayCallback";
    // Verified against LX04 IMicoDeviceServiceInterface.Stub: ubusRelay is transaction 12.
    private static final int UBUS_RELAY = 12;
    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private IBinder service;
    private boolean bound;
    private boolean closed;
    private String pending;
    private final Runnable bindingTimeout = () -> {
        if (!closed && pending != null) {
            pending = null;
            reportError("小爱语音暂时未连接，审批仍可正常使用");
        }
    };
    private final ServiceConnection connection = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName name, IBinder binder) {
            if (closed) return;
            service = binder;
            main.removeCallbacks(bindingTimeout);
            Log.i(TAG, "Connected to native XiaoAi device service");
            if (pending != null) {
                String text = pending;
                pending = null;
                speak(text);
            }
        }
        @Override public void onServiceDisconnected(ComponentName name) { service = null; }
    };

    XiaoAiSpeech(Context context) {
        this.context = context;
        bind();
    }

    private void bind() {
        if (bound || closed) return;
        Intent intent = new Intent().setComponent(new ComponentName("com.xiaomi.micolauncher",
            "com.xiaomi.micolauncher.common.services.deviceservice.MicoDeviceService"));
        try { bound = context.bindService(intent, connection, Context.BIND_AUTO_CREATE); }
        catch (RuntimeException e) { Log.w(TAG, "Native voice binding failed", e); }
    }

    void speak(String text) {
        if (closed) return;
        IBinder target = service;
        if (target == null) {
            pending = text;
            bind();
            main.removeCallbacks(bindingTimeout);
            main.postDelayed(bindingTimeout, 5000);
            return;
        }
        executor.execute(() -> {
            Parcel data = Parcel.obtain();
            Parcel reply = Parcel.obtain();
            try {
                JSONObject payload = new JSONObject();
                payload.put("tts_text", text);
                payload.put("show_ui", 0);
                Binder callback = new Binder() {
                    @Override protected boolean onTransact(int code, Parcel input, Parcel output, int flags)
                            throws RemoteException {
                        if (code == INTERFACE_TRANSACTION) {
                            if (output != null) output.writeString(CALLBACK);
                            return true;
                        }
                        if (code == FIRST_CALL_TRANSACTION) {
                            input.enforceInterface(CALLBACK);
                            String result = input.readString();
                            Log.i(TAG, "Native TTS response: " + result);
                            try {
                                if (new JSONObject(result).optInt("code", -1) != 0)
                                    reportError("小爱播报请求失败，审批结果已保留");
                            } catch (Exception e) { Log.w(TAG, "Invalid TTS response", e); }
                            if (output != null) output.writeNoException();
                            return true;
                        }
                        return super.onTransact(code, input, output, flags);
                    }
                };
                data.writeInterfaceToken(DESCRIPTOR);
                data.writeString("mibrain");
                data.writeString("ai_tts_request");
                data.writeString(payload.toString());
                data.writeStrongBinder(callback);
                if (!target.transact(UBUS_RELAY, data, reply, 0))
                    throw new RemoteException("Native TTS transaction unsupported");
                reply.readException();
                Log.i(TAG, "Native TTS requested: " + text);
            } catch (Exception e) {
                Log.w(TAG, "Native TTS request failed", e);
                reportError("小爱语音暂时不可用，审批仍可正常使用");
            } finally { reply.recycle(); data.recycle(); }
        });
    }

    private void reportError(String message) {
        main.post(() -> { if (!closed) Toast.makeText(context, message, Toast.LENGTH_LONG).show(); });
    }

    void close() {
        closed = true;
        pending = null;
        main.removeCallbacksAndMessages(null);
        if (bound) context.unbindService(connection);
        bound = false;
        service = null;
        executor.shutdownNow();
    }
}
