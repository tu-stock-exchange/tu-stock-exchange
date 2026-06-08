<template>
  <!-- background page-->
  <v-container fluid class="bg-black min-h-screen d-flex align-center justify-center">

    <!-- whole card -->
    <v-card width="420" rounded="xl" elevation="0" class="login-card">

      <!-- title -->
      <v-card-title class="text-white font-bold" style="font-size: 1.5rem;"> Create your account </v-card-title>

      <!-- title and subtitle -->
      <div class="px-6 pt-6 pb-2">
        <h2 class="text-white font-bold" style="font-size: 1.5rem;">  Create your account  </h2>
        <p class="text"> You start with $10,000 in virtual trading capital </p>
      </div>

      <!-- email, username, password and confirm password logic (until 147)-->
      <v-card-text class="px-6 pt-4">
        <v-form ref="form">
          <v-row dense justify="center">
            <v-col cols="11">

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
            </v-col>
        
            <v-col cols="11">
              <v-text-field
                v-model="username"
                :rules="usernameRules"
                label="Username"
                type="text"
                variant="outlined"
                rounded="lg"
                density="comfortable"
                bg-color="#27272A"
                base-color="#71717A"
                color="#EAB308"
                class="mb-3"
              > 
                <template v-slot:prepend-inner>
                  <User :size="20" class="text-zinc-500" />
                </template>
              </v-text-field>
            </v-col>
      
          <v-col cols="11">
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
          </v-col>

          <v-col cols="11">
            <v-text-field
              v-model="confirmPassword"
              :rules="confirmPasswordRules"
              label="Confirm Password"
              :type="showConfirmPassword ? 'text' : 'password'"
              variant="outlined"
              rounded="lg"
              density="comfortable"
              bg-color="#27272A"
              base-color="#71717A"
              color="#EAB308"
              class="mb-3"
            >
              <template v-slot:prepend-inner>
                <Lock :size="20" class="text-grey-darken-1" />
              </template>
              <template v-slot:append-inner>
                <Eye 
                  v-if="showConfirmPassword" 
                  :size="18" 
                  class="cursor-pointer text-grey-darken-1"
                  @click="showConfirmPassword = false"
                />
                <EyeOff 
                  v-else 
                  :size="18" 
                  class="cursor-pointer text-grey-darken-1"
                  @click="showConfirmPassword = true"
                />
              </template>
            </v-text-field>
          </v-col>
        </v-row>

          <!-- error message if conditions are not met-->
          <v-alert v-if="errorMessage" type="error" 
            variant="tonal"
            rounded="lg"
            class="mt-2">
            {{ errorMessage }}
          </v-alert>

        </v-form>
      </v-card-text>

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
          <UserPlus :size="18" class="mr-2" />
          Create account - start with $10,000
        </v-btn>

        <!-- just a divider-->
        <v-divider color="#27272A" class="mb-4" />

        <!-- last row; if the user already has an account he will be redirected to login by clicking on sign in-->
        <div class="d-flex align-center justify-center ga-1">
          <span class="text-zinc-500 text-sm">Already have an account?</span>
            <RouterLink to="/login" class="accent-link text-sm ml-1 font-medium">
              Sign in
            </RouterLink>
        </div>

      </v-card-actions>

    </v-card>
   
  </v-container>

</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import api from '@/api/axiosInstance' // IGOR: imported axios to call real API

  // lucide icons added
  import { 
    Mail,      
    Lock,      
    Eye,       
    EyeOff,    
    User, 
  } from 'lucide-vue-next'

  const email = ref('')
  const password = ref('')
  const loading = ref(false)
  const errorMessage = ref('')
  const form = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)
  const username = ref('')
  const confirmPassword = ref('')

  const router = useRouter()

  // const for the password visibility token
  const showPassword = ref(false)
  const showConfirmPassword = ref(false)


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

  const usernameRules = [
    (v: string) => !!v || 'Username is required',
    (v: string) => v.length >= 5 || 'Minimum 5 characters',
    (v: string) => v.length <= 20 || 'Maximum 20 characters',
    (v: string) => /^[a-zA-Z0-9_]+$/.test(v) || 'Only letters, numbers, and underscores allowed',
    (v: string) => !v.includes(' ') || 'Spaces are not allowed'
  ]

  const confirmPasswordRules = [
    (v: string) => !!v || 'Please confirm your password',
    (v: string) => v === password.value || 'Passwords do not match'
  ]

  async function onSubmit() {
    if (!form.value) return
    const { valid } = await form.value.validate()
    if (!valid) return

    loading.value = true
    errorMessage.value = ''

    try {
      // IGOR: replaced fake setTimeout with real API call
      // calls POST /auth/register with email, username and password
      await api.post('/auth/register', {
        email: email.value,
        username: username.value,
        password: password.value
      })

      // IGOR: after successful registration redirect to login
      // so user can sign in with their new account
      router.push('/login')

    } catch (error) {
      // IGOR: shows error if registration fails (email taken, server down, etc.)
      errorMessage.value = 'Registration failed. Please try again.'
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

  .text {
    color: #EAB308;
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