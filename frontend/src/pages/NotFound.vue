<!-- 404 page -->

<template>
  <!-- background page-->
  <v-container fluid class="bg-black min-h-screen d-flex align-center justify-center">

    <!-- card -->
    <v-card width="500" class="pa-10 text-center error-card" rounded="xl" elevation="0">

      <!-- text -->
      <div class="error-code">404</div>
      <h1 class="text-white font-bold" style="font-size: 1.5rem;"> Page not found </h1>
      <p class="text-zinc-500 text-sm mt-1"> This page doesn’t exist or has been moved. </p>

      <!-- space -->
      <div class="mb-6" />

      <!-- dashboard button -->
      <v-row justify="center">
        <v-col cols="10">
          <v-btn
            block
            to="/dashboard"
            size="large"
            rounded="lg"
            variant="flat"
            class="dash-btn font-bold mb-4"
          >
            <ArrowLeft :size="20" class="mr-2" />
            Back to dashboard
          </v-btn>
        </v-col>

        <!-- market button -->
        <v-col cols="10">
          <v-btn
            block
            to="/"
            size="large"
            rounded="lg"
            variant="flat"
            class="btn font-bold"
          >
            Go to market
          </v-btn>
        </v-col>
      </v-row>
      

    </v-card>

  </v-container>
  
</template>

<script setup lang="ts">
 
  // imports
  import { ArrowLeft } from 'lucide-vue-next'
  import { useAuthStore } from '@/stores/auth'
  const authStore = useAuthStore()

</script>



<style scoped>
.error-card {
  background-color: #18181B !important;
  border: 1px solid #27272A !important;
}

.error-code {
  font-size: 96px;
  font-weight: 800;
  line-height: 1;
  color: #EAB308 !important;
  margin-bottom: 16px;
}

.btn {
  background-color: #18181B !important;
  color: #71717A  !important;
  font-weight: 700;
  border: 1px solid #27272A !important;  /* border damit man ihn sieht */
}

.btn:hover {
  background-color: #27272A !important;
  color: #D4D4D8 !important;        /* heller beim hover */
}

.dash-btn {
  background-color: #EAB308 !important;
  color: #000000  !important;
  font-weight: 700;
  border: 1px solid #27272A !important;  /* border damit man ihn sieht */
}

.dash-btn:hover {
  background-color: #27272A !important;
  color: #D4D4D8 !important;        /* heller beim hover */
}

</style>

