<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'

const items = ref([])
const err = ref('')
const newDate = ref('')
const newFactor = ref(1.5)
const editId = ref(null)
const editDate = ref('')
const editFactor = ref(1)

const load = async () => { items.value = (await getJSON('/api/holidays')).items }
const guard = async (fn) => { err.value = ''; try { await fn(); await load() } catch (e) { err.value = e.message } }

const create = () => guard(async () => {
  await postJSON('/api/holidays', { service_date: newDate.value, factor: newFactor.value })
  newDate.value = ''
})
const startEdit = (h) => { editId.value = h.id; editDate.value = h.service_date; editFactor.value = h.factor }
const cancelEdit = () => { editId.value = null }
const saveEdit = (id) => guard(async () => {
  await putJSON(`/api/holidays/${id}`, { service_date: editDate.value, factor: editFactor.value })
  editId.value = null
})
const deactivate = (id) => guard(() => postJSON(`/api/holidays/${id}/deactivate`))
const activate = (id) => guard(() => postJSON(`/api/holidays/${id}/activate`))

onMounted(load)
</script>

<template>
  <div class="page"><h1>节假日系数</h1>
    <div class="panel">
      <label>服务日期 <input type="date" v-model="newDate" /></label>
      <label>系数 <input type="number" step="0.01" min="0.01" v-model.number="newFactor" /></label>
      <button @click="create" :disabled="!newDate">新增</button>
    </div>
    <p v-if="err" class="error">{{ err }}</p>
    <table>
      <tr><th>#</th><th>服务日期</th><th>系数</th><th>状态</th><th>操作</th></tr>
      <tr v-for="h in items" :key="h.id" :class="{ off: !h.active }">
        <template v-if="editId === h.id">
          <td>#{{ h.id }}</td>
          <td><input type="date" v-model="editDate" /></td>
          <td><input type="number" step="0.01" min="0.01" v-model.number="editFactor" /></td>
          <td>{{ h.active ? '启用' : '停用' }}</td>
          <td><button @click="saveEdit(h.id)">保存</button> <button @click="cancelEdit">取消</button></td>
        </template>
        <template v-else>
          <td>#{{ h.id }}</td>
          <td>{{ h.service_date }}</td>
          <td>×{{ h.factor }}</td>
          <td><span :class="h.active ? 'badge on' : 'badge'">{{ h.active ? '启用' : '停用' }}</span></td>
          <td>
            <button @click="startEdit(h)">编辑</button>
            <button v-if="h.active" @click="deactivate(h.id)">停用</button>
            <button v-else @click="activate(h.id)">启用</button>
          </td>
        </template>
      </tr>
    </table>
    <p v-if="!items.length" class="muted">暂无记录</p>
  </div>
</template>
