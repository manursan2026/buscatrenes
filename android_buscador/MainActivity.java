package com.manursan.buscadortrenes;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.provider.CalendarContract;
import android.util.Base64;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.regex.Pattern;

/**
 * Envoltorio mínimo: un WebView a pantalla completa que carga el buscador
 * (buscador_trenes.html, autocontenido) desde los assets. El buscador funciona
 * completamente offline; la red solo se usa (si la hay) para descargar las
 * incidencias en tiempo real vía el puente AndroidNet, que además esquiva el
 * bloqueo CORS del feed de RENFE. La geolocalización del HTML se puentea al
 * permiso de localización de Android.
 */
public class MainActivity extends Activity {

    private GeolocationPermissions.Callback geoCallback;
    private String geoOrigin;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView wv = new WebView(this);
        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(true);

        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(
                    String origin, GeolocationPermissions.Callback callback) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED) {
                    callback.invoke(origin, true, false);
                } else {
                    geoCallback = callback;
                    geoOrigin = origin;
                    requestPermissions(
                            new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                                         Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
                }
            }
        });

        // Puente para el botón "Compartir" del HTML: abre el panel nativo de Android
        wv.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void share(String texto) {
                Intent i = new Intent(Intent.ACTION_SEND);
                i.setType("text/plain");
                i.putExtra(Intent.EXTRA_TEXT, texto);
                startActivity(Intent.createChooser(i, "Compartir itinerario"));
            }
        }, "AndroidShare");

        // Puente para el botón "Calendario" del HTML: abre el editor de eventos
        // del calendario con el itinerario precargado (el usuario confirma allí)
        wv.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void evento(String titulo, String desc, String iniMs, String finMs) {
                try {
                    Intent i = new Intent(Intent.ACTION_INSERT)
                            .setData(CalendarContract.Events.CONTENT_URI)
                            .putExtra(CalendarContract.Events.TITLE, titulo)
                            .putExtra(CalendarContract.Events.DESCRIPTION, desc)
                            .putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, Long.parseLong(iniMs))
                            .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, Long.parseLong(finMs));
                    startActivity(i);
                } catch (Exception e) { /* sin app de calendario: no se hace nada */ }
            }
        }, "AndroidCal");

        // Puente de red para las incidencias en tiempo real: el JS pide una URL
        // https y recibe el cuerpo en base64 vía window.__netCb(id, b64|null).
        wv.addJavascriptInterface(new Object() {
            private final Pattern ID_OK = Pattern.compile("[0-9]+");

            @JavascriptInterface
            public void fetch(String url, String cbId) {
                if (cbId == null || !ID_OK.matcher(cbId).matches()) return;
                new Thread(() -> {
                    String b64 = null;
                    try {
                        URL u = new URL(url);
                        if (!"https".equals(u.getProtocol())) throw new Exception("solo https");
                        HttpURLConnection c = (HttpURLConnection) u.openConnection();
                        c.setConnectTimeout(10000);
                        c.setReadTimeout(15000);
                        try (InputStream in = c.getInputStream();
                             ByteArrayOutputStream bo = new ByteArrayOutputStream()) {
                            byte[] buf = new byte[8192];
                            int n;
                            while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                            b64 = Base64.encodeToString(bo.toByteArray(), Base64.NO_WRAP);
                        } finally {
                            c.disconnect();
                        }
                    } catch (Exception e) { /* sin red o error http: b64 = null */ }
                    final String arg = b64 == null ? "null" : "\"" + b64 + "\"";
                    wv.post(() -> wv.evaluateJavascript(
                            "window.__netCb(\"" + cbId + "\"," + arg + ")", null));
                }).start();
            }
        }, "AndroidNet");

        setContentView(wv);
        wv.loadUrl("file:///android_asset/buscador_trenes.html");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        if (requestCode == 1 && geoCallback != null) {
            boolean ok = results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED;
            geoCallback.invoke(geoOrigin, ok, false);
            geoCallback = null;
        }
    }
}
