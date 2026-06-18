<template>
    <Bar 
    :data = "chartData"
    :options = "chartOptions"
    />
  
</template>

<script setup lang="ts">


    import { computed } from 'vue'

    // import vue-chartjs for top 5 players leaderboard
    import { Bar } from 'vue-chartjs'
    import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

    ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

    // props
    const props = defineProps<{
        players: { username: string, portfolio_value: number }[]
    }>()

    const chartData = computed(() => ({
        labels: props.players.map(p => p.username),
        datasets: [{
            label: 'Portfolio Value',
            data: props.players.map(p => p.portfolio_value),
            backgroundColor: ['#F5C518', '#D4A017', '#6B7280', '#4B5563', '#374151']
        }]
    }))

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1.6,

        plugins: {
            legend: { display: false },
            layout: { 
                autoPadding: true 
            },
            title: {
                display: true,
                text: 'Top 5 Players',
                fullSize: true

            }
        }
        
    }

</script>