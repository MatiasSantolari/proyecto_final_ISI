(() => {
  const API = {
    kpis: '/dashboard/api/kpis/',
    vacations: '/dashboard/api/vacaciones/',
    attendance: '/dashboard/api/asistencias/',
    evaluations: '/dashboard/api/evaluaciones/',
    payroll: '/dashboard/api/nominas/',
    laboral_cost: '/dashboard/api/costo_laboral_comp/',
    structure: '/dashboard/api/estructura/',
    objectives: '/dashboard/api/objetivos/',
    capacitaciones: '/dashboard/api/capacitaciones/', 
  };

  // theme handling
  const root = document.documentElement;

  // Chart instances
  let vacChart=null, attendanceChart, evalChart=null, payrollChart, deptChart, laborCostChart = null, capChart = null;

  // helper to fetch json and safe fallback
  async function safeFetch(url){
    try{
      const res = await fetch(url, { credentials: 'same-origin' });
      if(!res.ok) throw new Error('Network response not ok');
      return await res.json();
    }catch(err){
      console.error('fetch error', url, err);
      return null;
    }
  }

  async function loadAll(){
      const kpis = await safeFetch(API.kpis);
      if(kpis){
          document.getElementById('kpiEmployees').innerText = kpis.employees_total ?? '0';
          document.getElementById('kpiAbsences').innerText = kpis.absences_count ?? '0';
          document.getElementById('kpiEvalAvg').innerText = kpis.eval_avg ? kpis.eval_avg.toFixed(2) : '0.00';
          
          if (kpis.payroll_cost) {
              document.getElementById('kpiPayroll').innerText = new Intl.NumberFormat('es-AR', {
                  style: 'currency', currency: 'ARS', maximumFractionDigits: 0
              }).format(kpis.payroll_cost);
          } else {
              document.getElementById('kpiPayroll').innerText = '$ 0';
          }

          document.getElementById('txtAbsenceMonth').innerText = kpis.absences_month_name || 'Actual';
          document.getElementById('txtPayrollMonth').innerText = kpis.payroll_month_name || 'Pasado';
          document.getElementById('txtEvalRange').innerText = kpis.eval_range || 'Anual';
    }


    function generateModernPalette(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 137.5) % 360; 
            colors.push(`hsl(${hue}, 65%, 55%)`);
        }
        return colors;
    }

    const structure = await safeFetch(API.structure);
    if (structure) {
        const ctx = document.getElementById('deptChart').getContext('2d');
        const labels = structure.labels || [];
        const data = structure.counts || [];
        const modernColors = generateModernPalette(labels.length);

        const parent = document.getElementById('deptChartParent');
        
        if (labels.length > 8) {
            parent.style.height = (labels.length * 45) + 'px';
        } else {
            parent.style.height = '100%'; 
        }

        if (!deptChart) {
            deptChart = new Chart(ctx, {
                type: 'bar',
                data: { 
                    labels, 
                    datasets: [{ 
                        label: 'Empleados', 
                        data,
                        backgroundColor: modernColors, 
                        borderRadius: 20,           
                        borderSkipped: false,
                        barPercentage: 0.7,         
                        categoryPercentage: 0.8,
                        hoverBackgroundColor: modernColors.map(c => c.replace('%)', ', 0.8)')), 
                    }]
                },
                options: { 
                    indexAxis: 'y', 
                    responsive: true,
                    maintainAspectRatio: false, 
                    layout: { padding: { top: 10, bottom: 10, left: 0, right: 25 } },
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 10,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: { label: (context) => ` ${context.raw} empleados` }
                        }
                    },
                    scales: {
                        x: { 
                            beginAtZero: true,
                            border: { display: false },
                            grid: { color: 'rgba(156, 163, 175, 0.1)', drawTicks: false },
                            ticks: {
                                stepSize: 1,
                                color: '#9ca3af',
                                callback: (value) => Number.isInteger(value) ? value : null
                            }
                        },
                        y: {
                            border: { display: false },
                            grid: { display: false }, 
                            ticks: {
                                color: '#9ca3af',
                                font: { size: 11, weight: '500' }
                            }
                        }
                    },
                    animation: { duration: 1200, easing: 'easeOutQuart' }
                }
            });
        } else { 
            deptChart.data.labels = labels; 
            deptChart.data.datasets[0].data = data; 
            deptChart.data.datasets[0].backgroundColor = modernColors;
            deptChart.update(); 
        }
    }

    
  }


  const centerTextPlugin = {
    id: 'centerText',
    beforeDatasetsDraw(chart, args, options) {
        const { ctx, data, chartArea: { top, bottom, left, right, width, height } } = chart;
        ctx.save();
        
        const totalValue = chart.canvas.dataset.totalVacations || '—'; 

        ctx.font = 'bold 32px sans-serif'; 
        ctx.fillStyle = '#b6b5b5ff'; 
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        const centerX = width / 2 + left;
        const centerY = height / 2 + top;

        ctx.fillText(totalValue, centerX, centerY);
        ctx.restore();
    }
  };


  let isFirstLoad = true;
  // Vacations
  async function loadVacations() {
    const periodSelector = document.getElementById('vacationPeriodSelector');
    const p = isFirstLoad ? '' : (periodSelector ? periodSelector.value : '1m');
    const apiUrl = `${API.vacations}?periodo=${p}`;
    
    const vac = await safeFetch(apiUrl);

    if(vac){
        if (isFirstLoad && vac.active_period && periodSelector) {
            periodSelector.value = vac.active_period;
            isFirstLoad = false; 
        }
        const dateRangeEl = document.getElementById('vacationDateRange');
        if (dateRangeEl && vac.start_date_formatted && vac.end_date_formatted) {
            const rangeText = (vac.start_date_formatted === vac.end_date_formatted)
                ? vac.start_date_formatted
                : `${vac.start_date_formatted} - ${vac.end_date_formatted}`;
            dateRangeEl.textContent = `(${rangeText})`;
        }

        const labels = ['Aprobadas', 'Pendientes', 'Rechazadas', 'Canceladas'];
        const rawValues = [vac.approved || 0, vac.pending || 0, vac.rejected || 0, vac.cancelled || 0];
        const customColors = ['#198754', '#ffc107', '#dc3545', '#adb5bd'];
        
        const total = rawValues.reduce((a, b) => a + b, 0);
        const hasData = total > 0;

        const chartValues = hasData ? rawValues : [1];
        const chartColors = hasData ? customColors : ['#e9ecef'];
        const chartLabels = hasData ? labels : ['Sin solicitudes'];

        document.getElementById('vacationTotalCenter').textContent = hasData ? total : '0';

        const legendContainer = document.getElementById('vacationCustomLegend');
        legendContainer.innerHTML = ''; 

        labels.forEach((label, i) => {
            const val = rawValues[i];
            const percentage = hasData ? ((val / total) * 100).toFixed(0) : '0';
            legendContainer.innerHTML += `
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <div class="d-flex align-items-center" style="min-width: 0;">
                        <div style="width: 3px; height: 18px; background-color: ${hasData ? customColors[i] : '#dee2e6'}; border-radius: 2px;" class="me-2"></div>
                        <div style="line-height: 1;">
                            <div style="font-size: 0.9rem; font-weight: 600;" class="text-truncate text-reset">${label}</div>
                            <small class="text-muted" style="font-size: 0.8rem;">${percentage}%</small>
                        </div>
                    </div>
                    <div class="text-end fw-bold" style="font-size: 0.8rem; min-width: 20px;">
                        ${val}
                    </div>
                </div>`;
        });

        const ctx = document.getElementById('vacChart').getContext('2d');
        
        if(!vacChart){
            vacChart = new Chart(ctx, {
                type: 'doughnut',
                data: { 
                    labels: chartLabels, 
                    datasets: [{ 
                        data: chartValues, 
                        backgroundColor: chartColors,
                        hoverOffset: hasData ? 6 : 0,
                        borderWidth: 0
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    cutout: '60%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: hasData,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 10,
                            cornerRadius: 6,
                            callbacks: {
                                label: (context) => ` ${context.label}: ${context.raw}`
                            }
                        }
                    }
                }
            });
        } else { 
            vacChart.data.labels = chartLabels;
            vacChart.data.datasets[0].data = chartValues; 
            vacChart.data.datasets[0].backgroundColor = chartColors; 
            vacChart.options.plugins.tooltip.enabled = hasData;
            vacChart.update(); 
        }
    }
  }




  async function loadAttendance() {
    const periodSelector = document.getElementById('attendancePeriodSelector');
    const selectedPeriod = periodSelector ? periodSelector.value : '30d';
    const apiUrl = `${API.attendance}?periodo=${selectedPeriod}`;

    const att = await safeFetch(apiUrl);
    if(att){
      const dateRangeEl = document.getElementById('attendanceDateRange');
      if (dateRangeEl && att.start_date_formatted && att.end_date_formatted) {
          const rangeText = (att.start_date_formatted === att.end_date_formatted)
              ? att.start_date_formatted
              : `${att.start_date_formatted} - ${att.end_date_formatted}`;
          dateRangeEl.textContent = `(${rangeText})`;
      }

      const ctx = document.getElementById('attendanceChart').getContext('2d');
      
      const extraLegendPadding = {
          id: 'extraLegendPadding',
          beforeInit(chart) {
              const originalFit = chart.legend.fit;
              chart.legend.fit = function fit() {
                  originalFit.bind(chart.legend)();
                  this.height += 25; 
              };
          }
      };

      if(!attendanceChart){
        attendanceChart = new Chart(ctx, {
          type: 'bar',
          plugins: [extraLegendPadding],
          data: {
            labels: att.labels || [],
            datasets: [
              { 
                label: 'Presentes', 
                data: att.present || [], 
                backgroundColor: '#28a745', 
                stack: 'stack1',
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7
              },
              { 
                label: 'Tardanzas', 
                data: att.late || [], 
                backgroundColor: '#ffc107', 
                stack: 'stack1',
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7
              },
              { 
                label: 'Ausencias', 
                data: att.ausent || [], 
                backgroundColor: '#dc3545', 
                stack: 'stack1',
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7
              }
            ]
          },
          options: { 
            responsive: true, 
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
                align: 'end',
                labels: {
                  usePointStyle: true,
                  pointStyle: 'circle',
                  padding: 15,
                  font: { size: 12, weight: '500' }
                }
              },
              tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                cornerRadius: 8
              }
            },
            scales: { 
              x: { 
                stacked: true,
                border: { display: false },
                grid: { display: false },
                ticks: { color: '#9ca3af' }
              }, 
              y: { 
                stacked: true,
                border: { display: false },
                grid: { color: 'rgba(156, 163, 175, 0.1)', drawTicks: false },
                ticks: {
                  stepSize: 1,
                  color: '#9ca3af',
                  callback: (value) => Number.isInteger(value) ? value : null
                }, 
                min: 0
              }
            }
          }
        });
      } else {
        attendanceChart.data.labels = att.labels;
        attendanceChart.data.datasets[0].data = att.present;
        attendanceChart.data.datasets[1].data = att.late;
        attendanceChart.data.datasets[2].data = att.ausent;
        attendanceChart.update();
      }
    }
  }


  // Evaluaciones
  async function loadEvaluations() {
      const periodSelector = document.getElementById('evalPeriodSelector');
      const selectedPeriod = periodSelector ? periodSelector.value : '12m';
      const apiUrl = `${API.evaluations}?periodo=${selectedPeriod}`;

      const evals = await safeFetch(apiUrl);
      if (evals) {
        const dateRangeEl = document.getElementById('evalDateRange');
        if (dateRangeEl && evals.start_date_formatted) {
          const rangeText = (evals.start_date_formatted === evals.end_date_formatted)
            ? evals.start_date_formatted
            : `${evals.start_date_formatted} - ${evals.end_date_formatted}`;
          dateRangeEl.textContent = `(${rangeText})`;
        }

        const ctx = document.getElementById('evalChart').getContext('2d');
        const labels = evals.labels || ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
        const data = evals.counts || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

        const colors = [
          '#dc3545', '#e4605e', '#ec8c77', '#f4b791', '#fce3aa',
          '#d4e9b1', '#abd9b8', '#82c9be', '#59b9c5', '#3c8dbc'
        ];

        if (!evalChart) {
          evalChart = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels,
              datasets: [{
                label: 'Cantidad',
                data: data,
                backgroundColor: colors, 
                borderRadius: 10,     
                borderSkipped: false,       
                barPercentage: 0.6,         
                categoryPercentage: 0.8,    
                hoverBackgroundColor: colors.map(c => c + 'CC'), 
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                  padding: 12,
                  cornerRadius: 8,
                  displayColors: false, 
                  callbacks: {
                    label: function(context) {
                      return ` Cantidad: ${context.raw} evaluaciones`;
                    }
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  border: { display: false }, 
                  ticks: {
                    stepSize: 1,      
                    precision: 0,
                    color: '#9ca3af' 
                  },
                  grid: {
                    color: 'rgba(156, 163, 175, 0.1)', 
                    drawTicks: false
                  }
                },
                x: {
                  border: { display: false },
                  ticks: {
                    color: '#9ca3af'
                  },
                  grid: { display: false } 
                }
              },
              animation: {
                  duration: 1500,
                  easing: 'easeOutQuart'
              }
            }
          });
        } else {
          evalChart.data.labels = labels;
          evalChart.data.datasets[0].data = data;
          evalChart.data.datasets[0].backgroundColor = colors;
          evalChart.update();
        }
      }

  }



  function formatAbbreviated(num) {
      if (num >= 1000000) return '$' + (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
      if (num >= 1000) return '$' + (num / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
      return '$' + num.toFixed(0);
  }

  async function loadPayroll() {
      const periodSelector = document.getElementById('payrollPeriodSelector');
      const selectedPeriod = periodSelector ? periodSelector.value : '1m';
      const apiUrl = `${API.payroll}?periodo=${selectedPeriod}`;

      const pay = await safeFetch(apiUrl);
      if (pay) {
        
          const labels = ['Sueldo Base', 'Beneficios', 'Descuentos', 'Extras'];
          const rawValues = [pay.base || 0, pay.benefits || 0, pay.discounts || 0, pay.extras || 0];
          const colors = ['#3c8dbc', '#28a745', '#dc3545', '#ffc107'];
          
          const total = rawValues.reduce((a, b) => a + b, 0);
          const hasData = total > 0;

          const chartValues = hasData ? rawValues : [1]; 
          const chartColors = hasData ? colors : ['#e9ecef'];
          const chartLabels = hasData ? labels : ['Sin datos registrados'];

          document.getElementById('payrollTotalCenter').textContent = hasData ? formatAbbreviated(total) : '$0';

          const legendContainer = document.getElementById('payrollCustomLegend');
          legendContainer.innerHTML = ''; 
          labels.forEach((label, i) => {
              const val = rawValues[i];
              const percentage = hasData ? ((val / total) * 100).toFixed(1) : '0';
              legendContainer.innerHTML += `
                  <div class="d-flex align-items-center justify-content-between mb-2">
                      <div class="d-flex align-items-center">
                          <div style="width: 4px; height: 22px; background-color: ${hasData ? colors[i] : '#dee2e6'}; border-radius: 2px;" class="me-2"></div>
                          <div style="line-height: 1.1;">
                              <div style="font-size: 1rem; font-weight: 600;" class="text-reset">${label}</div>
                              <small class="text-muted" style="font-size: 0.9rem;">${percentage}%</small>
                          </div>
                      </div>
                      <div class="text-end fw-bold" style="font-size: 0.9rem;">
                          ${hasData ? formatAbbreviated(val) : '-'}
                      </div>
                  </div>`;
          });

          const ctx = document.getElementById('payrollChart').getContext('2d');
          
          if (!payrollChart) {
              payrollChart = new Chart(ctx, {
                  type: 'doughnut',
                  data: {
                      labels: chartLabels,
                      datasets: [{
                          data: chartValues,
                          backgroundColor: chartColors,
                          borderWidth: 0,
                          hoverOffset: 6 
                      }]
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false,
                      cutout: '60%', 
                      plugins: {
                          legend: { display: false },
                          tooltip: {
                              enabled: hasData, 
                              callbacks: {
                                  label: function(context) {
                                      let label = context.label || '';
                                      let value = context.raw || 0;
                                      if (label) label += ': ';
                                      return label + formatAbbreviated(value);
                                  }
                              }
                          }
                      }
                  }
              });
          } else {
              payrollChart.data.labels = chartLabels;
              payrollChart.data.datasets[0].data = chartValues;
              payrollChart.data.datasets[0].backgroundColor = chartColors;
              payrollChart.options.plugins.tooltip.enabled = hasData;
              payrollChart.update();
          }

          const dateRangeEl = document.getElementById('payrollDateRange');
          if (dateRangeEl && pay.start_date_formatted) {
              const rangeText = (pay.start_date_formatted === pay.end_date_formatted) 
                  ? pay.start_date_formatted 
                  : `${pay.start_date_formatted} - ${pay.end_date_formatted}`;
              
              dateRangeEl.textContent = `Periodo: ${rangeText}`;
          }
      }
  }



  // Laboral Cost Comparison
  function populateYearSelectors() {
    const currentYear = new Date().getFullYear();
    const startYear = 2020; 
    
    const selector1 = document.getElementById('yearSelector1');
    const selector2 = document.getElementById('yearSelector2');

    selector1.innerHTML = '';
    selector2.innerHTML = '';

    for (let i = currentYear; i >= startYear; i--) {
        const option1 = new Option(i, i);
        const option2 = new Option(i, i);
        
        selector1.add(option1);
        selector2.add(option2);
    }
    
    selector1.value = currentYear - 1; 
    selector2.value = currentYear;
  }
  

  async function loadLaborCostComparison() {
      const selector1 = document.getElementById('yearSelector1');
      const selector2 = document.getElementById('yearSelector2');
      if (!selector1 || !selector2) return;

      const year1 = selector1.value;
      const year2 = selector2.value;

      const apiUrl = `${API.laboral_cost}?year1=${year1}&year2=${year2}`;
      const response = await safeFetch(apiUrl); 
      
      const chartCanvas = document.getElementById('laborCostComparisonChart');
      const noDataMessage = document.getElementById('noComparisonDataMessage');

      const isEmpty = !response || 
                      (response.data_year1.every(v => v === 0) && 
                      response.data_year2.every(v => v === 0));

      if (isEmpty) {
          if(chartCanvas) chartCanvas.style.opacity = '0';
          if(noDataMessage) noDataMessage.style.display = 'block';
          return; 
      }

      if(chartCanvas) chartCanvas.style.opacity = '1';
      if(noDataMessage) noDataMessage.style.display = 'none';

      const ctx = chartCanvas.getContext('2d');
      
      const grad1 = ctx.createLinearGradient(0, 0, 0, 350);
      grad1.addColorStop(0, 'rgba(0, 123, 255, 0.2)');
      grad1.addColorStop(1, 'rgba(0, 123, 255, 0)');

      const grad2 = ctx.createLinearGradient(0, 0, 0, 350);
      grad2.addColorStop(0, 'rgba(40, 167, 69, 0.2)');
      grad2.addColorStop(1, 'rgba(40, 167, 69, 0)');

      if (window.laborCostChart instanceof Chart) {
          window.laborCostChart.destroy();
      }

      window.laborCostChart = new Chart(ctx, {
          type: 'line',
          data: {
              labels: response.labels, 
              datasets: [{
                  label: `Año ${year1}`,
                  data: response.data_year1,
                  borderColor: '#007bff', 
                  backgroundColor: grad1,
                  fill: true,
                  tension: 0.4, 
                  borderWidth: 3,
                  pointRadius: 0,
                  pointHoverRadius: 6,
                  pointBackgroundColor: '#007bff',
              }, {
                  label: `Año ${year2}`,
                  data: response.data_year2,
                  borderColor: '#28a745', 
                  backgroundColor: grad2,
                  fill: true,
                  tension: 0.4, 
                  borderWidth: 3,
                  pointRadius: 0,
                  pointHoverRadius: 6,
                  pointBackgroundColor: '#28a745',
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                  mode: 'index',
                  intersect: false
              },
              plugins: {
                  legend: { display: false },
                  tooltip: {
                      mode: 'index',
                      intersect: false,
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      padding: 12,
                      cornerRadius: 8,
                      callbacks: {
                          label: (context) => ` ${context.dataset.label}: $${context.raw.toLocaleString()}`
                      }
                  }
              },
              scales: {
                  y: {
                      beginAtZero: true,
                      border: { display: false },
                      grid: { color: 'rgba(0, 0, 0, 0.05)', drawTicks: false },
                      ticks: {
                          color: '#9ca3af',
                          font: { size: 11 },
                          callback: (value) => '$' + value.toLocaleString()
                      }
                  },
                  x: {
                      border: { display: false },
                      grid: { display: false },
                      ticks: { color: '#9ca3af', font: { size: 11 } }
                  }
              },
              elements: {
                  point: {
                      radius: 0,          
                      hitRadius: 20,      
                      hoverRadius: 6,     
                      hoverBorderWidth: 3,
                      hoverBackgroundColor: '#fff' 
                  }
              }
          }
      });
  }



  async function loadObjectives() {
      const departmentSelector = document.getElementById('departmentSelector');
      const selectedDepartmentId = departmentSelector ? departmentSelector.value : 'todos';

      const apiUrl = selectedDepartmentId !== 'todos' 
          ? `${API.objectives}?departamento_id=${selectedDepartmentId}` 
          : API.objectives;

      const objs = await safeFetch(apiUrl);
      const list = document.getElementById('objectivesList');
      list.innerHTML = '';

      if(objs && objs.items && objs.items.length > 0){
        objs.items.forEach(o => {
          let progressClass = 'bg-primary'; 
          let textColor = 'text-primary';
          if (o.progress < 35) { progressClass = 'bg-danger'; textColor = 'text-danger'; }
          else if (o.progress < 75) { progressClass = 'bg-warning'; textColor = 'text-warning'; }
          else { progressClass = 'bg-success'; textColor = 'text-success'; }

          const wrap = document.createElement('div');
          
          wrap.className = 'p-3 mb-2 rounded-3 border d-flex flex-column';
          wrap.style.cssText = `
              background-color: rgba(128, 128, 128, 0.05); 
              border-color: rgba(128, 128, 128, 0.15) !important;
              transition: transform 0.2s ease;
          `;
          
          wrap.onmouseover = () => { wrap.style.transform = 'translateX(5px)'; wrap.style.backgroundColor = 'rgba(128, 128, 128, 0.1)'; };
          wrap.onmouseout = () => { wrap.style.transform = 'translateX(0)'; wrap.style.backgroundColor = 'rgba(128, 128, 128, 0.05)'; };

          wrap.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div style="max-width: 75%;">
                <div class="fw-bold text-reset" style="font-size: 0.85rem; line-height: 1.2;">
                  ${o.title}
                </div>
                <div class="text-muted mt-1" style="font-size: 0.7rem;">
                  <span class="badge border text-muted fw-normal" style="background: rgba(128,128,128,0.1); border-color: rgba(128,128,128,0.2) !important;">
                      ${o.type}
                  </span> 
                  <span class="ms-2">${o.owner || '—'}</span>
                </div>
              </div>
              <div class="fw-bolder ${textColor}" style="font-size: 0.85rem;">
                ${o.progress}%
              </div>
            </div>
            <div class="progress" style="height: 6px; background-color: rgba(128, 128, 128, 0.2); border-radius: 10px;">
              <div class="progress-bar ${progressClass}" role="progressbar" 
                  style="width: ${o.progress}%; border-radius: 10px; transition: width 1s ease;" 
                  aria-valuenow="${o.progress}" aria-valuemin="0" aria-valuemax="100">
              </div>
            </div>
          `;
          list.appendChild(wrap);
        });
      } else {
          list.innerHTML = `<div class="text-center py-5 text-muted small">No hay objetivos activos.</div>`;
      }
  }



  // Capacitaciones
  async function loadCapacitaciones() {
      const periodSelector = document.getElementById('capPeriodSelector');
      const selectedPeriod = periodSelector ? periodSelector.value : '6m';
      const apiUrl = `${API.capacitaciones}?periodo=${selectedPeriod}`;

      const data = await safeFetch(apiUrl);
      if(data) {
          const dateRangeEl = document.getElementById('capDateRange');
          if (dateRangeEl && data.start_date_formatted) {
              const rangeText = (data.start_date_formatted === data.end_date_formatted)
                  ? data.start_date_formatted
                  : `${data.start_date_formatted} - ${data.end_date_formatted}`;
              dateRangeEl.textContent = `(${rangeText})`;
          }

          const ctx = document.getElementById('capChart').getContext('2d');
          
          const extraLegendPadding = {
              id: 'extraLegendPadding',
              beforeInit(chart) {
                  const originalFit = chart.legend.fit;
                  chart.legend.fit = function fit() {
                      originalFit.bind(chart.legend)();
                      this.height += 20;
                  };
              }
          };

          if(!capChart) {
              capChart = new Chart(ctx, {
                  type: 'bar',
                  plugins: [extraLegendPadding],
                  data: {
                      labels: data.labels,
                      datasets: [
                          { 
                              label: 'Inscripciones Internas', 
                              data: data.internas, 
                              backgroundColor: '#3c8dbc', 
                              borderRadius: 20, 
                              borderSkipped: false,
                              barPercentage: 0.6, 
                              categoryPercentage: 0.7 
                          },
                          { 
                              label: 'Interés Externo', 
                              data: data.externas, 
                              backgroundColor: '#28a745', 
                              borderRadius: 20, 
                              borderSkipped: false,
                              barPercentage: 0.6,
                              categoryPercentage: 0.7
                          }
                      ]
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { 
                          legend: { 
                              position: 'top',
                              align: 'end',
                              labels: {
                                  usePointStyle: true, 
                                  pointStyle: 'circle',
                                  padding: 20,
                                  font: { size: 12, weight: '500' }
                              }
                          },
                          tooltip: {
                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                              padding: 12,
                              cornerRadius: 8,
                              callbacks: {
                                  label: (context) => ` ${context.dataset.label}: ${context.raw}`
                              }
                          }
                      },
                      scales: {
                          y: { 
                              beginAtZero: true, 
                              border: { display: false },
                              ticks: { 
                                  stepSize: 1,
                                  color: '#9ca3af',
                                  precision: 0 
                              },
                              grid: {
                                  color: 'rgba(156, 163, 175, 0.1)',
                                  drawTicks: false
                              }
                          },
                          x: { 
                              border: { display: false },
                              grid: { display: false },
                              ticks: { color: '#9ca3af' }
                          }
                      },
                      animation: {
                          duration: 1200,
                          easing: 'easeOutQuart'
                      }
                  }
              });
          } else {
              capChart.data.labels = data.labels;
              capChart.data.datasets[0].data = data.internas;
              capChart.data.datasets[1].data = data.externas;
              capChart.update();
          }
      }
  }


  document.addEventListener('DOMContentLoaded', (event) => {
    loadAll();
    loadObjectives();
    loadVacations();
    loadPayroll();
    loadAttendance();
    loadEvaluations();
    populateYearSelectors();
    loadLaborCostComparison(); 
    loadCapacitaciones();
    
    const selectorYear1 = document.getElementById('yearSelector1');
    const selectorYear2 = document.getElementById('yearSelector2');
    if (selectorYear1){
      selectorYear1.addEventListener('change', loadLaborCostComparison);
    }
    if (selectorYear2){
      selectorYear2.addEventListener('change', loadLaborCostComparison);
    }
    const selectorEvals = document.getElementById('evalPeriodSelector');
    if (selectorEvals) {
        selectorEvals.addEventListener('change', loadEvaluations);
    }
    const selectorAttendance = document.getElementById('attendancePeriodSelector');
    if (selectorAttendance) {
        selectorAttendance.addEventListener('change', loadAttendance);
    }
    const selectorPayRoll = document.getElementById('payrollPeriodSelector');    
    if (selectorPayRoll) {
        selectorPayRoll.addEventListener('change', loadPayroll);
    }
    const selectorVacations = document.getElementById('vacationPeriodSelector');
    if (selectorVacations) {
        selectorVacations.addEventListener('change', loadVacations);
    }
    const selectorObjetives = document.getElementById('departmentSelector');
    if (selectorObjetives) {
        selectorObjetives.addEventListener('change', loadObjectives);
    }
    const selectorCap = document.getElementById('capPeriodSelector');
    if (selectorCap) selectorCap.addEventListener('change', loadCapacitaciones);
  });

})();
