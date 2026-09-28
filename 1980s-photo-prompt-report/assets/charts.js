(function () {
  var chartEl = document.getElementById('trends-chart');
  if (!chartEl || typeof echarts === 'undefined') return;

  var chart = echarts.init(chartEl, null, { renderer: 'svg' });

  var option = {
    backgroundColor: 'transparent',
    animation: false,
    grid: {
      left: 50,
      right: 30,
      top: 30,
      bottom: 50
    },
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      backgroundColor: '#161332',
      borderColor: '#2d2858',
      textStyle: { color: '#e8e6f0', fontSize: 12 },
      axisPointer: {
        type: 'shadow',
        shadowStyle: { color: 'rgba(255, 46, 136, 0.08)' }
      }
    },
    legend: {
      data: ['每日搜索量 (次)', '增长趋势'],
      textStyle: { color: '#8580a8', fontSize: 11 },
      bottom: 5,
      itemWidth: 12,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: ['9月3日', '9月4日', '9月5日', '9月6日', '9月7日', '9月8日', '9月9日', '9月10日', '9月11日', '9月12日'],
      axisLine: { lineStyle: { color: '#2d2858' } },
      axisLabel: { color: '#8580a8', fontSize: 10, fontFamily: 'DMMono, monospace' },
      axisTick: { show: false }
    },
    yAxis: [
      {
        type: 'value',
        name: '搜索量',
        nameTextStyle: { color: '#8580a8', fontSize: 11 },
        axisLine: { show: false },
        axisLabel: {
          color: '#8580a8',
          fontSize: 10,
          fontFamily: 'DMMono, monospace',
          formatter: function (v) {
            if (v >= 1000) return (v / 1000) + 'k';
            return v;
          }
        },
        splitLine: { lineStyle: { color: 'rgba(232, 230, 240, 0.06)' } }
      },
      {
        type: 'value',
        name: '增长率',
        nameTextStyle: { color: '#8580a8', fontSize: 11 },
        axisLine: { show: false },
        axisLabel: {
          color: '#8580a8',
          fontSize: 10,
          fontFamily: 'DMMono, monospace',
          formatter: '{value}%'
        },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '每日搜索量 (次)',
        type: 'bar',
        data: [2000, 8000, 25000, 80000, 200000, 350000, 500000, 420000, 300000, 220000],
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#ff2e88' },
              { offset: 1, color: 'rgba(255, 46, 136, 0.2)' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '40%'
      },
      {
        name: '增长趋势',
        type: 'line',
        yAxisIndex: 1,
        data: [0, 300, 1150, 1900, 3500, 4200, 5000, 3800, 2500, 1600],
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { color: '#00e5ff', width: 2 },
        itemStyle: { color: '#00e5ff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 229, 255, 0.15)' },
              { offset: 1, color: 'rgba(0, 229, 255, 0)' }
            ]
          }
        }
      }
    ]
  };

  chart.setOption(option);

  var resize = function () { chart.resize(); };
  window.addEventListener('resize', resize);
})();
