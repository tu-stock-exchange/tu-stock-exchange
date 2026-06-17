<template>
  
  <v-dialog :model-value="modelValue" :persistent="!closeOnOverlay" width="400">
    <v-card class="modal-card">

      <v-card-title class="modal-title">{{ title }}</v-card-title>
      <v-card-text class="modal-text">{{ confirmationText }}</v-card-text>

      <v-card-actions class="pa-4 pt-0 d-flex ga-3">
        <v-btn
          block
          variant="flat"
          class="modal-btn-cancel"
          rounded="lg"
          @click="emit('cancel'); emit('update:modelValue', false)"
        >
          Cancel
        </v-btn>
        <v-btn
          block
          variant="flat"
          class="modal-btn-confirm"
          rounded="lg"
          @click="emit('confirm'); emit('update:modelValue', false)"
        >
          Confirm
        </v-btn>
      </v-card-actions>

    </v-card>
  </v-dialog>
  
</template>

<script setup lang="ts">

const props = withDefaults(defineProps<{
  title: string
  modelValue: boolean
  confirmationText: string
  // make the last attribute optional
  closeOnOverlay?: boolean
}>(), {
  closeOnOverlay: true,
})

const emit = defineEmits<{
  confirm: []
  cancel: []
  'update:modelValue' : [value: boolean]
}>()


</script>

<style scoped>

  .modal-card {
    background-color: #18181B !important;
    border: 1px solid #3F3F46 !important;
    border-radius: 12px !important;
    padding: 0.5rem;
  }

  .modal-title {
    color: #FFFFFF !important;
    font-size: 1.125rem !important;
    font-weight: 700;
    padding-bottom: 0.25rem;
  }

  .modal-text {
    color: #71717A !important;
    font-size: 0.875rem !important;
    line-height: 1.5;
  }

  .modal-btn-cancel {
    background-color: #27272A !important;
    color: #D4D4D8 !important;
    font-weight: 700;
  }

  .modal-btn-confirm {
    background-color: #EF4444 !important;
    color: #FFFFFF !important;
    font-weight: 700;
  }

</style>