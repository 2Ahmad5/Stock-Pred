<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import Navbar from '../../components/Navbar/+page.svelte';
    import {openDB} from 'idb';
    import {
        Chart,
        DoughnutController,
        ArcElement,
        Tooltip,
        Legend,
        CategoryScale,
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        Title,
        Filler,
        ScatterController,
        TimeScale
    } from 'chart.js';
    import 'chartjs-adapter-luxon';

    import * as Table from "$lib/components/ui/table";
    import Calender from '../../components/Calender/+page.svelte'

    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController, TimeScale);


    let first_line_chart;


    let results = {};
    let summary = {};
    let tbl_summary = {};
    let mid_values = {}

    let startMonth = '';
    let endMonth = '';
    let startDate = '';
    let endDate = '';
    let ticker = "";
    let model = "";
    let constraint = "";

    let isFocused = false;
    let submit = false;

    let years = [];
    let suggestions = [];
    let etflist = [];
    let models = ["CAPM", "FF3", "FF4", "FF5"];
    let mid_titles = []


    for (let year = 1970; year <= 2024; year++) {
        years.push(year);
    }    

    let months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    onMount(async () => {
        const db = await openDB('csvStore', 1, {
        upgrade(db) {
            db.createObjectStore('keyval');
        },
        });

        const storedEtfList = await db.get('keyval', 'etfList');

        if (storedEtfList) {
            etflist = storedEtfList;

        }else{ 
            const response = await fetchCsv('/ETF_tickers_only.csv');
            etflist = response;
            await db.put('keyval', etflist, 'etfList');
        }
    
    });

    function updateSuggestions(value){
        suggestions = etflist
        .filter(ticker => ticker.toLowerCase().includes(value.toLowerCase()))
        .slice(0, 3);
    }

    function handleFocus(){
        isFocused = true;
    }

    function handleBlur(){
        isFocused = false;
    }

    function selectSuggestion(suggestion){
        ticker = suggestion;
        suggestions = [];
    }

    function formatToYYYYMM(dateString) {
        if (!dateString) return '';
        const [year, month] = dateString.split('-');
        return `${year}${month}`;
    }

    function handleSubmit(){
        startDate = formatToYYYYMM(startMonth)
        endDate = formatToYYYYMM(endMonth)
        console.log(startDate, endDate)
        
    }

    function handleStartMonth(event) {
        startMonth = event.detail.monthYear;
    }

    function handleEndMonth(event) {
        endMonth = event.detail.monthYear;
    }

    async function processInput(){
        try{
            await axios.post('http://127.0.0.1:5000/run_regress', {
                Tick: ticker,
                Start: Number(`${startDate}`),
                End: Number(`${endDate}`),
                Mod: model
            }).then((response) => {
                return new Promise((resolve, reject) => {
                    
                    resolve(response)
                })
            }).then((response) => {
                submit = true;
                results = response.data;
                summary = results.mdl_summary;
                tbl_summary = results.tbl_summary;
                mid_titles = results.mid_titles;
                mid_values = results.mid_values;
                constraint = results.constraint;
                console.log(results.line_graph_6)
                updateChartData(
                results.line_graph_1?.[0] ?? {}, 
                results.line2?.[0] ?? {}, 
                results.line3?.[0] ?? {}, 
                results.line4?.[0] ?? {}, 
                results.line5?.[0] ?? {}, 
                results.line6?.[0] ?? {}
            );
            })


        } catch (error) {
            console.error('Error:', error);
        }
    }

    function updateChartData(fl, sl, tl, forl, fil, sil){

        
        const ctx = document.querySelector('.first-line-chart').getContext('2d');

        if (first_line_chart) {
            first_line_chart.destroy();
        }

        // Ensure all datasets are defined, default to an empty object with data: []
        const allDatasets = [fl, sl, tl, forl, fil, sil].map(dataset => dataset ?? { label: '', data: [] });

        // Filter datasets safely by ensuring dataset and its data exist
        const filteredDatasets = allDatasets.filter(dataset => dataset.data && Array.isArray(dataset.data) && dataset.data.length > 0);

        // If no valid datasets exist, prevent chart rendering to avoid errors
        if (filteredDatasets.length === 0) {
            console.warn('⚠️ No valid data to display in the chart.');
            return;
        }

        first_line_chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: filteredDatasets.map((dataset, index) => ({
                    type: 'line',
                    label: dataset.label,
                    data: dataset.data,
                    borderColor: dataset.borderColor || 'gray',
                    borderWidth: dataset.borderWidth || 1,
                    pointRadius: dataset.pointRadius || 2,
                    fill: false,
                    yAxisID: index === 0 ? 'y' : 'y1',
                    borderDash: index > 1 ? [index * 2, index * 4] : [],
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'year'
                        }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: {
                            color: 'red'
                        },
                        title: {
                            display: true,
                            text: 'Annualized Alpha',
                            color: 'red'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: {
                            color: 'orange'
                        },
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Factor Loadings',
                            color: 'orange'
                        }
                    }
                }
            }
        });
        }

    onMount(() => {
        const ctx = document.querySelector('.first-line-chart').getContext('2d');
        first_line_chart = new Chart(ctx, {
            data: {
                labels: [],
                datasets: [{
                    type: 'line',
                    label: 'Data',
                    data: [],
                }]
            },
            options: {
                // @ts-ignore
                borderWidth: 10,
                borderRadius: 2,
                hoverBorderWidth: 0,
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });
    })



</script>

<body>

    <Navbar/>
    <div class="w-screen h-screen grid reg-page">

        <div class="flex flex-col items-end justify-center">
            <h2 class="text-lg  w-[40%] mb-[3vh]">Start Date (Year, Month)</h2>
            <div class="grid grid-cols-2 w-[40%] gap-[1vw]">
                <Calender bind:selectedMonthYear={startMonth} on:monthSelected={handleStartMonth} />
            </div>
            <h2 class="text-lg w-[40%] mt-[5vh] mb-[3vh]">End Date (Year, Month)</h2>
            <div class="grid grid-cols-2 w-[40%] gap-[1vw]">
                <Calender bind:selectedMonthYear={endMonth} on:monthSelected={handleEndMonth} />
            </div>
            <h2 class="text-lg w-[40%] mt-[5vh] mb-[3vh]">Ticker</h2>
            <div class="relative w-[40%]">
                <input
                    class=" h-[5vh] hover:border-[#5ce07f] border-[#A9A9A9] p-[10px] border-2 rounded-md outline-none"
                    type="text"
                    placeholder="Place ticker here..."
                    bind:value={ticker}
                    on:input={(e) => updateSuggestions(e.target.value)}
                    on:focus={() => handleFocus()}
                    on:blur={() => setTimeout(() => handleBlur(), 500)}
                >
                {#if isFocused && suggestions.length > 0}
                    <ul class="absolute bg-[#2c2e2f] w-[40%] border border-gray-300 mt-1 rounded-md z-10 outline-none">
                    {#each suggestions as suggestion}
                        <option class="p-2 rounded-md hover:bg-[#131217] cursor-pointer"  on:click={() => selectSuggestion(suggestion)}>
                        {suggestion}
                        </option>
                    {/each}
                    </ul>
                {/if}
            </div>
            <h2 class="text-lg w-[40%] mt-[5vh] mb-[3vh]">Model</h2>
            <div class="w-[40%]">
                <select class="border-2 flex hover:border-[#5ce07f] justify-center items-center w-[40%] rounded h-[4vh] border-[#A9A9A9] text-base pl-[5%]" bind:value={model}>
                    {#each models as mod}
                    <option class="text-sm rounded" value={mod}>{mod}</option>
                    {/each}
                </select>
            </div>
            <div class="w-[40%]">
                <button class="mt-[5vh] py-[10px] px-[30px] text-xl text-black rounded-md border-[#A9A9A9] hover:bg-[#282828] hover:text-[#5ce07f] hover:border-[#696a6b] ease-in-out duration-150 border-2 border-[#5ce07f] bg-[#5ce07f]" on:click={handleSubmit} on:click={processInput}>Submit</button>
            </div>

        </div>
        <div class="flex flex-col items-center justify-center pt-[10vh]">
            <h1 class="text-2xl mb-[5vh]">36-Month Rolling Regression</h1>
            <div class="programming-stats max-h-[80vh] w-[60vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[60vw] first-line-chart"></canvas>
            </div>
            <p class="text-[#8c8c8c] text-sm mt-[1vh] text-center">{constraint}</p>
        </div>
        

    </div>
    {#if submit}
    <div class="w-screen items-center">
        <h1 class="text-xl text-center">OLS Regression Results</h1>
        <div class="flex flex-col items-center">
            <div class="w-[60vw] text-gray-100 p-8">
                <div class="max-w-7xl mx-auto">
                  <div class="grid grid-cols-4 gap-4 mb-12">
                    {#each Object.entries(summary) as [key, value]}
                      <div class="bg-[#242627] rounded-lg shadow-lg p-4 flex justify-between items-center">
                        <p class="text-xs text-gray-400">{key}</p>
                        <p class="text-xs text-[#C0C0C0]">{value}</p>
                      </div>
                    {/each}
                  </div>
              
                  
                </div>
            </div>
            <div class="w-[60vw] overflow-x-auto rounded-lg shadow-lg p-4">
                <table class="w-full">
                  <thead>
                    <tr class="border-b text-gray-400 border-gray-700">
                      <th class="p-2 text-left"></th>
                      <th class="p-2 text-center">coef</th>
                      <th class="p-2 text-center">std err</th>
                      <th class="p-2 text-center">t</th>
                      <th class="p-2 text-center">P>|t|</th>
                      <th class="p-2 text-center">[0.025]</th>
                      <th class="p-2 text-center">[0.975]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each Object.entries(mid_values) as [rowKey, values]}
                      <tr class="border-b border-gray-700 hover:bg-gray-750 transition-colors duration-200">
                        <th class="p-2 text-gray-400 text-left font-medium">{rowKey}</th>
                        {#each values as value}
                          <td class="p-2 text-sm text-center text-[#C0C0C0]">{value}</td>
                        {/each}
                      </tr>
                    {/each}
                  </tbody>
                </table>
            </div>
            <div class="w-[60vw] flex flex-col text-gray-100 p-8">
                <div class="w-full max-w-4xl mx-auto mt-10">
                  <Table.Root>
                    <Table.Header>
                      <Table.Row>
                        <Table.Head></Table.Head>
                        <Table.Head>Av. Ann. Excess Return</Table.Head>
                        <Table.Head>Return Contribution</Table.Head>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {#each Object.entries(tbl_summary) as [rowKey, rowValue]}
                        <Table.Row>
                          <Table.Head>{rowKey}</Table.Head>
                          {#each Object.values(rowValue) as cellValue}
                            <Table.Cell class="text-[#C0C0C0]">
                              {cellValue}
                              
                            </Table.Cell>
                          {/each}
                        </Table.Row>
                      {/each}
                    </Table.Body>
                </Table.Root>
                </div>
              </div>
            
        </div>

        
    </div>
    {/if}


</body>

<style>
@import '../../app.css';

.reg-page{
    grid-template-columns: 30vw 70vw;
    /* background: #1b1b1b; */
    /* background: linear-gradient(to bottom, #181818, #0e0f13); */

}

.programming-stats {
    font-family: 'Rubik', sans-serif;
    display: flex;
    justify-content: end;
    /* align-items: center; */
    gap: 24px;
    margin: 0 auto;
    /* width: fit-content; */
    box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.3);
    border-radius: 20px;
    padding: 8px 32px;
    color: white;
    transition: all 400ms ease;
    /* background-color: #2e3233; */
}
.programming-stats:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 16px -7px rgba(0, 0, 0, 0.6);
}
.programming-stats .details ul {
    list-style: none;
    padding: 0;
}



.data-item{
    transition: all 400ms ease;
}

.data-item:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 16px -7px rgba(0, 0, 0, 0.3);
}


</style>