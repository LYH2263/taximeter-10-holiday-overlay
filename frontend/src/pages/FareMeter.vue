<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const service_date = ref('')
const out = ref(null)
const err = ref('')

const calc = async (persist) => {
  err.value = ''
  try {
    out.value = await postJSON('/api/fare', {
      distance_km: distance_km.value,
      slow_min: slow_min.value,
      night: night.value,
      service_date: service_date.value || null,
      persist,
    })
  } catch (e) { err.value = e.message }
}
const trial = () => calc(false)   // 只读试算，不写记录
const submit = () => calc(true)   // 打表提交，落库
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <label>服务日期 <input type="date" v-model="service_date" /></label>
      <button @click="trial">只读试算</button>
      <button class="primary" @click="submit">打表提交</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <div v-if="out" class="panel result">
      <p class="hero-num">¥{{ out.total }}</p>
      <p>起步 ¥{{ out.start }} · 里程 ¥{{ out.mileage }} · 低速 ¥{{ out.slow_fee }}</p>
      <p class="hint">
        夜间系数 ×{{ out.night_factor }}
        <template v-if="out.holiday_factor">
          · 节假日系数 ×{{ out.holiday_factor }}（命中启用日期 {{ out.service_date || service_date }}，记录 #{{ out.holiday_id }}）
        </template>
        <template v-else>· 无节假日系数（未填日期或未命中）</template>
      </p>
      <p v-if="out.run_id" class="hint">已写入打表记录 #{{ out.run_id }}</p>
      <p v-else class="hint">本次为只读试算，未写入记录</p>
    </div>
  </div>
</template>
