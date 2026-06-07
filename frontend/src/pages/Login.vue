<template>

  <v-container fluid class="bg-black min-h-screen d-flex align-center justify-center">

    <!-- whole card -->
    <v-card width="420" rounded="xl" elevation="0" class="login-card">

      <!-- title and subtitle -->
      <div class="px-6 pt-6 pb-2">
        <h2 class="text-white font-bold" style="font-size: 1.5rem;">Welcome back</h2>
        <p class="text-zinc-500 text-sm mt-1">Sign in to continue trading</p>
      </div>

      <v-card-text class="px-6 pt-4">
        <v-form ref="form">

          <!-- for the email input field -->
          <v-text-field
            v-model="email"
            :rules="emailRules"
            label="Email"
            type="email"
            variant="outlined"
            rounded="lg"
            density="comfortable"
            bg-color="#27272A"
            base-color="#71717A"
            color="#EAB308"
            class="mb-2"
          >
            <!-- lucide icon for mail added-->
            <template v-slot:prepend-inner>
              <Mail :size="20" class="text-zinc-500" />
            </template>
          </v-text-field>

          <!-- for the password input field -->
          <v-text-field
            v-model="password"
            :rules="passwordRules"
            label="Password"
            :type="showPassword ? 'text' : 'password'"
            variant="outlined"
            rounded="lg"
            density="comfortable"
            bg-color="#27272A"
            base-color="#71717A"
            color="#EAB308"
            class="mb-3"
          >

          <!-- lucide icon added-->
            <template v-slot:prepend-inner>
              <Lock :size="20" class="text-zinc-500" />
            </template>

            <!-- lucide icon logic added so that the user can look or hide his password-->
            <template v-slot:append-inner>
              <Eye
                v-if="showPassword"
                :size="18"
                class="cursor-pointer text-zinc-500"
                @click="showPassword = false"
              />
              <EyeOff
                v-else
                :size="18"
                class="cursor-pointer text-zinc-500"
                @click="showPassword = true"
              />
            </template>
          </v-text-field>

          <!-- checkbox if the user want to stay logged in -->
          <div class="d-flex align-center justify-space-between mb-4">
            <label class="d-flex align-center ga-2 text-zinc-500 text-sm cursor-pointer">
              <input type="checkbox" v-model="rememberMe" class="accent-yellow-500" />
              Remember me
            </label>

            <!-- if user forgot password then he will be redirected to 404 page since forgot password page is not implemented-->
            <RouterLink to="/forgot-password" class="accent-link text-sm">
              Forgot password?
            </RouterLink>
          </div>

          <!-- handles the errors if the rules are not met-->
          <v-alert v-if="errorMessage" type="error" variant="tonal" rounded="lg" class="mb-4">
            {{ errorMessage }}
          </v-alert>

        </v-form>
      </v-card-text>

      <!-- logic for the sign in button -->
      <v-card-actions class="flex-column align-stretch px-6 pb-6 pt-0">

        <v-btn
          block
          size="large"
          @click="onSubmit"
          variant="flat"
          :loading="loading"
          rounded="lg"
          class="sign-in-btn font-bold mb-4"
        >
          <!-- lucide icon added -->
          <LogIn :size="18" class="mr-2" />
          Sign in
        </v-btn>

        <!-- just a divider-->
        <v-divider color="#27272A" class="mb-4" />

        <!-- last row; if the user doesn t have an account he will be redirected to register by clicking on sign up-->
        <div class="d-flex align-center justify-center ga-1">
          <span class="text-zinc-500 text-sm">Don't have an account?</span>
          <RouterLink to="/register" class="accent-link text-sm ml-1 font-medium">
            Sign up
          </RouterLink>
        </div>

      </v-card-actions>

    </v-card>

  </v-container>

</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '@/stores/auth' // IGOR: imported auth store to handle real login

  const showPassword = ref(false)

  // lucide icons
  import { 
    Mail,      
    Lock,      
    Eye,       
    EyeOff,    
    LogIn   
  } from 'lucide-vue-next'

  const email = ref('')
  const password = ref('')
  const loading = ref(false)
  const errorMessage = ref('')
  const rememberMe = ref(false)
  const form = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)

  const router = useRouter()
  const authStore = useAuthStore() // IGOR: initialized auth store

  const emailRules = [
    (v: string) => !!v || 'Email address is required',
    (v: string) => /.+@.+\..+/.test(v) || 'Email must be valid'
  ]

  const passwordRules = [
    (v: string) => !!v || 'Password is required',
    (v: string) => v.length >= 8 || 'Minimum 8 characters',
    (v: string) => /[a-z]/.test(v) || 'At least 1 lowercase letter',
    (v: string) => /[A-Z]/.test(v) || 'At least 1 uppercase letter',
    (v: string) => /[\d\W]/.test(v) || 'At least 1 number or special character'
  ]

  async function onSubmit() {
    if (!form.value) return
    const { valid } = await form.value.validate()
    if (!valid) return

    loading.value = true
    errorMessage.value = ''

    try {
      // IGOR: replaced fake setTimeout with real API call
      // authStore.login() calls POST /auth/login and saves token to localStorage
      await authStore.login(email.value, password.value)

      // IGOR: redirect to dashboard after successful login (was redirecting to '/')
      router.push('/dashboard')

    } catch (error) {
      // IGOR: shows error if API call fails (wrong credentials or backend down)
      errorMessage.value = 'Invalid username or password'
    } finally {
      loading.value = false
    }
  }
</script>


<style scoped>
  /*  for the whole card  — gives the black background color */
  .login-card {
    background-color: #18181B !important;
    border: 1px solid #27272A !important;
  }

  /* sign in button - yellow background */
  .sign-in-btn {
    background-color: #EAB308 !important;
    color: #000000 !important;
    font-weight: 700;
    letter-spacing: 0.01em;
  }

  .sign-in-btn:hover {
    background-color: #ca8a04 !important;
  }

  /* links like forgot password and sign up */
  .accent-link {
    color: #EAB308;
    text-decoration: none;
    font-weight: 500;
  }
  .accent-link:hover {
    color: #ca8a04;
  }

  /* opacity of the border around the input box */
  :deep(.v-field__outline) {
    --v-field-border-opacity: 1;
  }

  /* label text */
  :deep(.v-label) {
    color: #71717A !important;
  }

  /* label colour - we don t use the default white, instead we have the yellow */
  :deep(.v-field--focused .v-label) {
    color: #EAB308 !important;
  }

  /* border colour */
  :deep(.v-field--focused .v-field__outline) {
    color: #EAB308 !important;
  }

  /* written text by the user inside the input box */
  :deep(.v-field__input) {
    color: #D4D4D8 !important;
  }

  /* message under an input box if rules (passwort+email) are not met */
  :deep(.v-messages__message) {
    color: #F87171 !important;
  }

  /* oly used when loading is true after user clicked the sign in button */
  :deep(.v-btn__loader .v-progress-circular) {
    color: #000000 !important;
  }
</style>
