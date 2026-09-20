<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const service_date = ref('')
const out = ref(null)
const err = ref('')
const run = async () => {
  err.value = ''
  try {
    out.value = await postJSON('/api/fare', { distance_km: distance_km.value, slow_min: slow_min.value, night: night.value, service_date: service_date.value || null, persist: true })
  } catch (e) { err.value = e.message }
}
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label>服务日期 <input type="date" v-model="service_date" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <button @click="run">计算</button>
    </div>
    <p v-if="err" class="error">{{ err }}</p>
    <div v-if="out" class="panel">
      <p class="hero-num">¥{{ out.total }}</p>
      <p>起步 {{ out.start }} · 里程 {{ out.mileage }} · 低速 {{ out.slow_fee }}</p>
      <template v-if="out.holiday">
        <p><span class="badge on">节假日</span> {{ out.holiday.service_date }} · 系数 ×{{ out.holiday.factor }}</p>
        <p class="muted">乘前：起步 {{ out.pre_holiday.start }} · 里程 {{ out.pre_holiday.mileage }} · 低速 {{ out.pre_holiday.slow_fee }} · 应付 {{ out.pre_holiday.total }}</p>
      </template>
      <p v-else class="muted">未命中节假日系数</p>
    </div>
  </div>
</template>
