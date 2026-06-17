<template>

  <v-container fluid class="page-container d-flex align-center justify-center">

    <v-card width="420" rounded="xl" elevation="0" class="default-card pa-6">

      <!-- emoji -->
      <div class="emoji-circle d-flex align-center justify-center mb-5"> 💸 </div>

      <!-- title -->
      <div class="bankrupt-title mb-4"> You've gone bankrupt </div>

      <!-- small box -->
      <div class="info-box mb-4">
        Your net worth dropped below $100, triggering automatic default. All holdings have been liquidated.
      </div>

      <!-- divider -->
      <v-divider color="#27272A" class="mb-4" />

      <!-- text -->
      <div class="start-text mb-4"> Start over with a fresh balance: </div>

      <!-- two buttons -->
      <div class="d-flex flex-column ga-3">
        <v-btn
          block
          size="large"
          variant="flat"
          class="btn-restart"
          rounded="lg"
          @click="showModal = true"
        >
          Restart with $1,000
        </v-btn>

        <v-btn
          block
          size="large"
          variant="flat"
          class="btn-history"
          rounded="lg"
          @click="router.push('/profile')"
        >
          View final portfolio history
        </v-btn>
      </div>

    </v-card>

    <Modal
      v-model="showModal"
      title="Are you sure?"
      confirmationText="You will restart with $1,000. All your holdings will be liquidated."
      @confirm="onStartOver"
      @cancel="showModal = false"
    />

  </v-container>

</template>

<script setup lang="ts">

    import { useRouter } from 'vue-router'  
    import { ref } from 'vue'
    import Modal from '../components/shared/Modal.vue'

    const router = useRouter()

    function onStartOver () {
        // user gets redirected to dashboard page to reset the balance
        router.push('/dashboard')
    }

    const showModal = ref(false)

</script>


<style scoped>

  .page-container {
    background-color: #000000;
    min-height: 100vh;         /* fixes the small container */
    min-width: 100vw;
  }

  .default-card {
    background-color: #18181B !important;
    border: 1px solid #27272A !important;
  }

  .emoji-circle {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background-color: #3f1010;
    font-size: 2.5rem;
    margin: 0 auto;
  }

  .bankrupt-title {
    color: #F87171;
    font-size: 1.5rem;
    font-weight: 700;
    text-align: center;
  }

  .info-box {
    background-color: #1f0d0d;
    border: 1px solid #F87171;
    border-radius: 8px;
    color: #F87171;
    font-size: 0.875rem;
    line-height: 1.5;
    padding: 0.875rem 1rem;
    text-align: center;
  }

  .start-text {
    color: #D4D4D8;
    text-align: center;
  }

  .btn-restart {
    background-color: #EF4444 !important;
    color: #FFFFFF !important;
    font-weight: 700;
  }

  .btn-history {
    background-color: #27272A !important;
    color: #71717A !important;
    font-weight: 700;
  }

  /* modal css logic */
  :deep(.modal-overlay) {
    background-color: rgba(0, 0, 0, 0.75);
  }

  :deep(.modal-card) {
    background-color: #18181B !important;
    border: 1px solid #3F3F46 !important;
    border-radius: 12px;
  }

  :deep(.modal-title) {
    color: #FFFFFF;
    font-size: 1.125rem;
    font-weight: 700;
  }

  :deep(.modal-text) {
    color: #71717A;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  :deep(.modal-btn-cancel) {
    background-color: #27272A !important;
    color: #D4D4D8 !important;
    border-radius: 8px;
  }

  :deep(.modal-btn-confirm) {
    background-color: #EF4444 !important;
    color: #FFFFFF !important;
    font-weight: 700;
    border-radius: 8px;
  }

</style>
