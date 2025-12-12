(() => {
  const API = {
    kpis: '/dashboard/api/kpis/',
    vacations: '/dashboard/api/vacaciones/',
    attendance: '/dashboard/api/asistencias/',
    evaluations: '/dashboard/api/evaluaciones/',
    payroll: '/dashboard/api/nominas/',
    laboral_cost: '/dashboard/api/costo_laboral_comp/',
    structure: '/dashboard/api/estructura/',
    objectives: '/dashboard/api/objetivos/'
  };

  // theme handling
  const root = document.documentElement;

  // Chart instances
  let vacChart=null, attendanceChart, evalChart=null, payrollChart, deptChart, laborCostChart = null;

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
    // KPIs
    const kpis = await safeFetch(API.kpis);
    if(kpis){
      document.getElementById('kpiEmployees').innerText = kpis.employees_total ?? '—';
      document.getElementById('kpiAbsences').innerText = kpis.absences_month ?? '—';
      document.getElementById('kpiPayroll').innerText = kpis.payroll_cost_month ? `$ ${kpis.payroll_cost_month}` : '—';
      document.getElementById('kpiEvalAvg').innerText = kpis.eval_avg ? kpis.eval_avg.toFixed(2) : '—';
    }



    // structure (departments)
    const structure = await safeFetch(API.structure);
    if(structure){
      const ctx = document.getElementById('deptChart').getContext('2d');
      const labels = structure.labels || [];
      const data = structure.counts || [];
      if(!deptChart){
        deptChart = new Chart(ctx, {
          type: 'bar',
          data: { labels, datasets:[{ label: 'Empleados', data }]},
          options:{ 
            indexAxis: 'y',
            scales: {
              x: { 
                ticks: {
                  stepSize: 1, 
                  callback: function(value, index, values) {
                    if (Number.isInteger(value)) {
                      return value;
                    }
                  }
                },
                min: 0
              }
            },
            plugins:{
              legend:{
                display:false
              }
            }
          }
        });
      } else { deptChart.data.labels = labels; deptChart.data.datasets[0].data = data; deptChart.update(); }
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



  // Vacations
  async function loadVacations() {
    const periodSelector = document.getElementById('vacationPeriodSelector');
    const selectedPeriod = periodSelector ? periodSelector.value : '1m';

    const apiUrl = `${API.vacations}?periodo=${selectedPeriod}`;
    const vac = await safeFetch(apiUrl);

    if(vac){
      const totalCount = vac.total ?? '—';
      document.getElementById('vacChart').dataset.totalVacations = totalCount;
      
      const labels = ['Aprobadas','Pendientes','Rechazadas','Canceladas'];
      const data = [vac.approved || 0, vac.pending || 0, vac.rejected || 0, vac.cancelled || 0];
      const customColors = [
              '#198754', 
              '#ffc107', 
              '#dc3545', 
              '#b4b9baff'  
          ];
      if(!vacChart){
        const ctx = document.getElementById('vacChart').getContext('2d');
        vacChart = new Chart(ctx, {
          type: 'doughnut',
          data: { 
            labels, 
            datasets: [{ 
              data, 
              backgroundColor: customColors,
              hoverOffset:6, 
              radius: '85%',
            }]
          },
          options: { 
            plugins:{
              legend:{
                position:'bottom'
              }
            }
          },
          plugins: [centerTextPlugin]
        });
      } else { 
        vacChart.data.datasets[0].data = data; 
        vacChart.data.datasets[0].backgroundColor = customColors; 
        vacChart.update(); 
      }
    }
  
  }



    // attendance
  async function loadAttendance() {
    const periodSelector = document.getElementById('attendancePeriodSelector');
    const selectedPeriod = periodSelector ? periodSelector.value : '30d';
    const apiUrl = `${API.attendance}?periodo=${selectedPeriod}`;
  
    const att = await safeFetch(apiUrl);
    if(att){
      const dateRangeEl = document.getElementById('attendanceDateRange');
      if (dateRangeEl && att.start_date_formatted && att.end_date_formatted) {
          const rangeText = `${att.start_date_formatted} - ${att.end_date_formatted}`;
          dateRangeEl.textContent = `(${rangeText})`;
      } else if (dateRangeEl) {
          dateRangeEl.textContent = '';
      }

      const ctx = document.getElementById('attendanceChart').getContext('2d');
      const labels = att.labels || [];
      const present = att.present || [];
      const late = att.late || [];
      const ausent = att.ausent || [];
      
      if(!attendanceChart){
        attendanceChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels,
            datasets: [
              { label: 'Presentes', data: present, stack: 'stack1' },
              { label: 'Ausencias', data: ausent, stack: 'stack1' },
              { label: 'Tardanzas', data: late, stack: 'stack1' }
            ]
          },
          options: { 
            scales: { 
              x:{ 
                stacked:true 
              }, 
              y:{ 
                stacked:true,
                ticks:{
                  stepSize: 1,
                  callback: function(value, index, values) {
                    if (Number.isInteger(value)) {
                      return value;
                } 
              } 
            }, 
            min: 0
          }
        },
            plugins:{
              legend:{
                position:'bottom'
              }
            }
          }
        });
      } else {
        attendanceChart.data.labels = labels;
        attendanceChart.data.datasets[0].data = present;
        attendanceChart.data.datasets[2].data = ausent;
        attendanceChart.data.datasets[1].data = late;
        attendanceChart.update();
      }
    }
  }



    // evaluations
  async function loadEvaluations() {
    const periodSelector = document.getElementById('evalPeriodSelector');
    const selectedPeriod = periodSelector ? periodSelector.value : '12m';
    const apiUrl = `${API.evaluations}?periodo=${selectedPeriod}`;

    const evals = await safeFetch(apiUrl);
    if(evals){
      const dateRangeEl = document.getElementById('evalDateRange');
      if (dateRangeEl && evals.start_date_formatted && evals.end_date_formatted) {
          const rangeText = `${evals.start_date_formatted} - ${evals.end_date_formatted}`;
          dateRangeEl.textContent = `(${rangeText})`;
      } else if (dateRangeEl) {
          dateRangeEl.textContent = '';
      }
    
      const ctx = document.getElementById('evalChart').getContext('2d');
      const labels = evals.labels || ["1","2","3","4","5","6","7","8","9","10"];
      const data = evals.counts || [0,0,0,0,0,0,0,0,0,0];
      if(!evalChart){
        evalChart = new Chart(ctx, {
          type: 'bar',
          data: { labels, datasets: [{ label: 'Cantidad', data }]},
          options:{ plugins:{legend:{display:false}}}
        });
      } else { 
        evalChart.data.labels = labels;
        evalChart.data.datasets[0].data = data; 
        evalChart.update(); 
      }
    }
  }


    // payroll
  async function loadPayroll() {
    const periodSelector = document.getElementById('payrollPeriodSelector');
    const selectedPeriod = periodSelector ? periodSelector.value : '1m';
    const apiUrl = `${API.payroll}?periodo=${selectedPeriod}`;

    const pay = await safeFetch(apiUrl);
    if(pay){

      const dateRangeEl = document.getElementById('payrollDateRange');
      if (dateRangeEl) {
        if (pay.start_date_formatted && pay.end_date_formatted) {
            let rangeText;
            if (pay.start_date_formatted === pay.end_date_formatted) {
                rangeText = `${pay.start_date_formatted}`;
            } else {
                rangeText = `${pay.start_date_formatted} - ${pay.end_date_formatted}`;
            }
            dateRangeEl.textContent = `(${rangeText})`;
        } else {
            dateRangeEl.textContent = '';
        }
      }

      const ctx = document.getElementById('payrollChart').getContext('2d');
      const labels = ['Sueldo Base','Beneficios','Descuentos','Extras'];
      const data = [pay.base||0, pay.benefits||0, pay.discounts||0, pay.extras||0];
      if(!payrollChart){
        payrollChart = new Chart(ctx, {
          type: 'pie',
          data: { labels, datasets:[{ 
            data,
            radius: '80%' 
          }]},
          options:{ plugins:{legend:{position:'bottom'}}}
        });
      } else { 
        payrollChart.data.datasets[0].data = data; 
        payrollChart.update(); 
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
    const year1 = document.getElementById('yearSelector1').value;
    const year2 = document.getElementById('yearSelector2').value;

    if (!year1 || !year2) {
        console.error("Selectores de año no encontrados o vacíos.");
        return;
    }
    const apiUrl = `${API.laboral_cost}?year1=${year1}&year2=${year2}`;
    const response = await safeFetch(apiUrl); 
    
    const chartCanvas = document.getElementById('laborCostComparisonChart');
    const noDataMessage = document.getElementById('noComparisonDataMessage');

    const allDataZeroYear1 = response.data_year1.every(item => item === 0);
    const allDataZeroYear2 = response.data_year2.every(item => item === 0);
    
    if (!response || (allDataZeroYear1 && allDataZeroYear2)) {
        chartCanvas.style.display = 'none';
        noDataMessage.style.display = 'block';
        if (laborCostChart) laborCostChart.destroy();
        return; 
    }

    chartCanvas.style.display = 'block';
    noDataMessage.style.display = 'none';

    const ctx = chartCanvas.getContext('2d');
    if (laborCostChart) {
        laborCostChart.destroy();
    }

    laborCostChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: response.labels, 
            datasets: [{
                label: `Costo ${response.year1_label}`,
                data: response.data_year1,
                borderColor: '#007bff', 
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                tension: 0.4, 
                fill: false,
                pointBackgroundColor: '#007bff',
            }, {
                label: `Costo ${response.year2_label}`,
                data: response.data_year2,
                borderColor: '#28a745', 
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4, 
                fill: false,
                pointBackgroundColor: '#28a745',
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Costo Monetario ($)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Mes del Año'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
            },
            elements: {
                line: {
                    borderWidth: 2
                },
                point: {
                    radius: 4, 
                    hoverRadius: 6
                }
            }
        }
    });
  }



// objectives list
  async function loadObjectives() {
    const departmentSelector = document.getElementById('departmentSelector');
    const selectedDepartmentId = departmentSelector ? departmentSelector.value : 'todos';

    let apiUrl = API.objectives;
    if (selectedDepartmentId && selectedDepartmentId !== 'todos') {
        apiUrl += `?departamento_id=${selectedDepartmentId}`;
    }

    const objs = await safeFetch(apiUrl);
    const list = document.getElementById('objectivesList');
    list.innerHTML = '';
    if(objs && objs.items && objs.items.length > 0){
      objs.items.forEach(o=>{
        const wrap = document.createElement('div');
        wrap.className = 'd-flex justify-content-between align-items-center p-2 border rounded';
        wrap.innerHTML = `
          <div>
            <div class="fw-semibold">${o.title}</div>
            <div class="small-muted">${o.type} • ${o.owner || '—'}</div>
          </div>
          <div style="width:40%;">
            <div class="small-muted mb-1 text-end">${o.progress}%</div>
            <div class="progress" style="height:8px">
              <div class="progress-bar" role="progressbar" style="width: ${o.progress}%;" aria-valuenow="${o.progress}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>
        `;
        list.appendChild(wrap);
      });
    } else {
        list.innerHTML = `
            <div class="alert alert-info mt-3" role="alert">
                No hay objetivos activos para este departamento en este momento.
            </div>
        `;
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
  });

})();
