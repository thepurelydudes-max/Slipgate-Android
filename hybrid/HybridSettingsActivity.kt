package io.github.romanvht.byedpi.activities

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.text.InputType
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import io.github.romanvht.byedpi.services.HybridProfiles
import org.json.JSONArray
import org.json.JSONObject

class HybridSettingsActivity : Activity() {
    private lateinit var url: EditText
    private lateinit var selected: Spinner
    private lateinit var enabled: CheckBox
    private lateinit var domains: EditText
    private lateinit var status: TextView
    private var state = JSONObject()
    private var nodes = JSONArray()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        state = HybridProfiles.load(this) ?: JSONObject()
        nodes = state.optJSONArray("nodes") ?: JSONArray()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28,32,28,32)
        }
        fun label(s: String) = TextView(this).apply {
            text = s
            textSize = 16f
            setPadding(0,16,0,8)
            layout.addView(this)
        }
        label("Slipgate 0.4.0 — гибридный режим")
        label("Основной маршрут: ByeDPI. TikTok, ChatGPT и дополнительные домены — выбранный узел подписки. Отключённый гибрид не запускает sing-box.")
        url = EditText(this).apply {
            hint = if (state.has("url")) "Ссылка сохранена локально (вставь новую при необходимости)" else "HTTPS-ссылка подписки SpeedFix"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
            isSingleLine = true
            layout.addView(this)
        }
        val refresh = Button(this).apply { text = "Загрузить / обновить подписку" }
        layout.addView(refresh)
        refresh.setOnClickListener { fetch() }
        label("Сервер")
        selected = Spinner(this)
        layout.addView(selected)
        updateNodes()
        enabled = CheckBox(this).apply {
            text = "Включить выборочную маршрутизацию через SpeedFix"
            isChecked = state.optBoolean("enabled",false)
            layout.addView(this)
        }
        label("Дополнительные домены через SpeedFix, по одному в строке")
        domains = EditText(this).apply {
            setText(state.optString("domains",""))
            hint = "example.com"
            minLines = 3
            layout.addView(this)
        }
        status = TextView(this).apply {
            setPadding(0,16,0,16)
            text = getSharedPreferences("slipgate_hybrid_status",0)
                .getString("last_error","") ?: ""
            layout.addView(this)
        }
        layout.addView(Button(this).apply {
            text = "Сохранить и применить после переподключения"
            setOnClickListener { save() }
        })
        layout.addView(Button(this).apply {
            text = "Открыть настройки экономии батареи Android"
            setOnClickListener {
                try {
                    startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + packageName)))
                } catch (_: Exception) {
                    startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
                }
            }
        })
        label("Для Telegram MTProto/WS оставь службу включённой в самом Telegram-разделе. На Xiaomi/POCO дополнительно разреши работу в фоне. Отказ от экономии батареи может увеличить расход.")
        val scroller = ScrollView(this)
        scroller.addView(layout)
        setContentView(scroller)
    }
    private fun updateNodes() {
        val labels = (0 until nodes.length()).map {
            nodes.optJSONObject(it)?.optString("name","Server") ?: "Server"
        }.ifEmpty { listOf("Сначала загрузите подписку") }
        selected.adapter = ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,labels)
        selected.setSelection(state.optInt("selected",0).coerceIn(0,labels.size-1))
    }
    private fun fetch() {
        val next = url.text.toString().trim().ifEmpty { state.optString("url","") }
        if (!next.startsWith("https://")) {
            status.text = "Нужна HTTPS-ссылка подписки"
            return
        }
        status.text = "Загружаю подписку…"
        Thread {
            try {
                val result = HybridProfiles.fetch(next)
                val arr = JSONArray()
                result.forEach { arr.put(it) }
                runOnUiThread {
                    nodes = arr
                    state.put("url",next)
                    state.put("nodes",arr)
                    state.put("selected",0)
                    updateNodes()
                    status.text = "Получено серверов: " + result.size
                    url.text.clear()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    // Do not display a provider URL or a credential in an exception message.
                    status.text = "Ошибка импорта: " + e.javaClass.simpleName +
                        ". Проверь формат подписки и соединение."
                }
            }
        }.start()
    }
    private fun save() {
        if (enabled.isChecked && nodes.length() == 0) {
            status.text = "Сначала импортируй сервер."
            return
        }
        try {
            val entered = url.text.toString().trim()
            if (entered.isNotEmpty()) {
                require(entered.startsWith("https://"))
                state.put("url",entered)
            }
            state.put("nodes",nodes)
            state.put("selected",selected.selectedItemPosition.coerceAtLeast(0))
            state.put("enabled",enabled.isChecked)
            state.put("domains",domains.text.toString())
            HybridProfiles.save(this,state)
            status.text = "Сохранено. Отключи и включи Slipgate."
            Toast.makeText(this,"Настройки сохранены",Toast.LENGTH_SHORT).show()
        } catch (_: Exception) { status.text = "Не удалось сохранить настройки." }
    }
}
