<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, patchJSON, postJSON } from '../api'
const items = ref([])
const err = ref('')
const form = ref({ service_date: '', factor: 1.5, note: '', active: true })
const editing = ref({})

const load = async () => { items.value = (await getJSON('/api/holidays')).items }
const resetErr = () => { err.value = '' }
const create = async () => {
  resetErr()
  if (!form.value.service_date) { err.value = '请选择服务日期'; return }
  if (!(Number(form.value.factor) > 0)) { err.value = '系数必须大于零'; return }
  try {
    await postJSON('/api/holidays', {
      service_date: form.value.service_date,
      factor: Number(form.value.factor),
      note: form.value.note || null,
      active: form.value.active,
    })
    form.value.note = ''
    await load()
  } catch (e) { err.value = e.message }
}
const saveFactor = async (row) => {
  resetErr()
  const v = Number(editing.value[row.id])
  if (!(v > 0)) { err.value = `#${row.id} 系数必须大于零`; return }
  try {
    await patchJSON(`/api/holidays/${row.id}`, { factor: v })
    await load()
  } catch (e) { err.value = e.message }
}
const toggle = async (row) => {
  resetErr()
  try {
    await patchJSON(`/api/holidays/${row.id}`, { active: !row.active })
    await load()
  } catch (e) { err.value = e.message }
}
onMounted(load)
</script>
<template>
  <div class="page"><h1>节假日系数</h1>
    <p class="hint">维护服务日期与系数（系数须大于 0）；同一日期只允许一条启用。</p>
    <p v-if="err" class="err">{{ err }}</p>
    <div class="panel">
      <label>服务日期 <input type="date" v-model="form.service_date" @change="resetErr" /></label>
      <label>系数 <input type="number" step="0.01" min="0.01" v-model="form.factor" /></label>
      <label>备注 <input type="text" v-model="form.note" placeholder="如：春节" /></label>
      <label class="chk"><input type="checkbox" v-model="form.active" /> 立即启用</label>
      <button @click="create">新增</button>
    </div>
    <table>
      <tr><th>#</th><th>服务日期</th><th>系数</th><th>状态</th><th>备注</th><th>操作</th></tr>
      <tr v-for="r in items" :key="r.id">
        <td>#{{ r.id }}</td>
        <td>{{ r.service_date }}</td>
        <td>
          <input type="number" step="0.01" min="0.01" :value="r.id in editing ? editing[r.id] : r.factor"
                 @input="editing[r.id] = $event.target.value" style="width:6rem" />
          <button class="mini" @click="saveFactor(r)">保存</button>
        </td>
        <td>
          <span :class="r.active ? 'tag-on' : 'tag-off'">{{ r.active ? '启用中' : '已停用' }}</span>
        </td>
        <td>{{ r.note }}</td>
        <td><button class="mini" @click="toggle(r)">{{ r.active ? '停用' : '启用' }}</button></td>
      </tr>
      <tr v-if="!items.length"><td colspan="6">暂无节假日系数记录</td></tr>
    </table>
  </div>
</template>
