<template>
    <Line
      :data="chartData"
      :options="chartOptions"
    />
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue'
  import { Line } from 'vue-chartjs'
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Filler,
  } from 'chart.js'
  
  ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale, Filler)
  
  const props = defineProps<{
    history: { timestamp: string, net_worth: number }[]
  }>()
  
  const chartData = computed(() => {
    const isUp = props.history.length < 2
      || props.history[props.history.length - 1].net_worth >= props.history[0].net_worth
  
    return {
      labels: props.history.map(h =>
        new Date(h.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      ),
      datasets: [{
        label: 'Net worth',
        data: props.history.map(h => h.net_worth),
        borderColor: isUp ? '#34D399' : '#F87171',
        backgroundColor: isUp ? 'rgba(52, 211, 153, 0.12)' : 'rgba(248, 113, 113, 0.12)',
        pointBackgroundColor: isUp ? '#34D399' : '#F87171',
        pointBorderColor: isUp ? '#34D399' : '#F87171',
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      }],
    }
  })
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 3,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Net worth over time',
        color: '#D4D4D8',
        font: { size: 14, weight: 'bold' as const  },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `$${ctx.parsed.y.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: '#27272A' },
        ticks: { color: '#71717A' },
      },
      y: {
        grid: { color: '#27272A' },
        ticks: {
          color: '#71717A',
          callback: (value: number) => `$${value.toLocaleString()}`,
        },
      },
    },
  }
  </script>