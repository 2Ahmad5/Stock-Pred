<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import Navbar from '../../Navbar/+page.svelte';
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


    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController, TimeScale);


    let first_line_chart;


    let results = {};
    let summary = {};
    let tbl_summary = {};

    let startYear = "";
    let endYear = "";
    let startMonth = "";
    let endMonth = "";
    let ticker = "";
    let model = "";

    let isFocused = false;
    let submit = false;

    let years = [];
    let suggestions = [];
    let etflist = [];
    let models = ["CAPM", "FF3", "FF4", "FF5"];

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

            console.log(etflist);
        }else{ 
            const response = await fetchCsv('/ETF_tickers_only.csv');
            etflist = response;
            console.log(etflist)

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

    function handleSubmit(){
        if (months[startMonth] >= 1 && months[startMonth] <= 9){
            startMonth = `0${months[startMonth]}`
        } else{
            startMonth = `${months[startMonth]}`
        }
        if (months[endMonth] >= 1 && months[endMonth] <= 9){
            endMonth = `0${months[endMonth]}`
        } else{
            endMonth = `${months[endMonth]}`
        }
    }

    async function processInput(){
        try{
            await axios.post('http://127.0.0.1:5001/process2', {
                Tick: ticker,
                Start: Number(`${startYear}${startMonth}`),
                End: Number(`${endYear}${endMonth}`),
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
                console.log(tbl_summary);


                updateChartData(results.line_graph_1[0], results.line2[0], results.line3[0], results.line4[0]);
            })


        } catch (error) {
            console.error('Error:', error);
        }
    }

    function updateChartData(fl, sl, tl, forl){

        

        const ctx = document.querySelector('.first-line-chart').getContext('2d');

        if(first_line_chart){
            first_line_chart.destroy();
        }

        console.log(fl);

        first_line_chart = new Chart(ctx, {
            type: 'line',
            data: {
              
              

                datasets: [{
                    type: 'line',
                    label: fl.label,
                    data: fl.data,
                    borderColor: fl.borderColor,
                    borderWidth: fl.borderWidth,
                    pointRadius: fl.pointRadius,
                    fill: false,
                    yAxisID: 'y'
                },
                {
                    type: 'line',
                    label: sl.label,
                    data: sl.data,
                    borderColor: sl.borderColor,
                    borderWidth: sl.borderWidth,
                    pointRadius: sl.pointRadius,
                    fill: false,
                    yAxisID: 'y1'
                },
                {
                    type: 'line',
                    label: tl.label,
                    data: tl.data,
                    borderColor: tl.borderColor,
                    borderWidth: tl.borderWidth,
                    pointRadius: tl.pointRadius,
                    borderDash: [10, 5],
                    fill: false,
                    yAxisID: 'y1'
                },
                {
                    type: 'line',
                    label: forl.label,
                    data: forl.data,
                    borderColor: forl.borderColor,
                    borderWidth: forl.borderWidth,
                    pointRadius: forl.pointRadius,
                    borderDash: [2, 2],
                    fill: false,
                    yAxisID: 'y1'
                }
            ]

                
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

        <div class="flex flex-col bg-[#5ce07f] items-center justify-center">
            <h2 class="text-xl w-[80%] mb-[3vh]">Start Date (Year, Month)</h2>
            <div class="grid grid-cols-2 w-[80%] gap-[1vw]">
                <select class="border-2 flex justify-center items-center w-full rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={startYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded w-full h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={startMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
            </div>
            <h2 class="text-xl w-[80%] mt-[5vh] mb-[3vh]">End Date (Year, Month)</h2>
            <div class="grid grid-cols-2 w-[80%] gap-[1vw]">
                <select class="border-2 flex justify-center items-center w-full rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={endYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded w-full h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={endMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
            </div>
            <h2 class="text-xl w-[80%] mt-[5vh] mb-[3vh]">Ticker</h2>
            <div class="relative w-[80%]">
                <input
                    class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
                    type="text"
                    placeholder="Place ticker here..."
                    bind:value={ticker}
                    on:input={(e) => updateSuggestions(e.target.value)}
                    on:focus={() => handleFocus()}
                    on:blur={() => setTimeout(() => handleBlur(), 500)}
                >
                {#if isFocused && suggestions.length > 0}
                    <ul class="absolute bg-white border border-gray-300 w-full mt-1 rounded-md z-10 outline-none">
                    {#each suggestions as suggestion}
                        <option class="p-2 hover:bg-gray-200 cursor-pointer"  on:click={() => selectSuggestion(suggestion)}>
                        {suggestion}
                        </option>
                    {/each}
                    </ul>
                {/if}
            </div>
            <h2 class="text-xl w-[80%] mt-[5vh] mb-[3vh]">Model</h2>
            <div class="w-[80%]">
                <select class="border-2 flex justify-center items-center w-[50%] rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" bind:value={model}>
                    {#each models as mod}
                    <option class="text-sm rounded" value={mod}>{mod}</option>
                    {/each}
                </select>
            </div>
            <div class="w-[80%]">
                <button class="mt-[5vh] py-[10px] px-[30px] text-xl rounded-md bg-white ease-in-out duration-150 border-2 border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>
            </div>

        </div>
        <div class="flex items-center justify-center pt-[10vh]">
            <div class="programming-stats h-[80vh] w-[80vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[50vh] first-line-chart"></canvas>
            </div>
        </div>
        

    </div>
    {#if submit}
    <div class="w-screen h-screen items-center">
        <h1 class="text-2xl mt-[15vh] text-center">OLS Regression Results</h1>
        <div class="grid grid-cols-2">
            <div class="flex flex-col items-center">
            
                <div class="grid grid-cols-2 grid-rows-9 w-[40vw] mt-[10vh] gap-[1vw]">
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Dep. Variable: </p></div><div class="mr-[10%]"><p>{summary["Dep. Variable"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>R-squared: </p></div><div class="mr-[10%]"><p>{summary["R-squared"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Model: </p></div><div class="mr-[10%]"><p>{summary["Model"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Adj. R-squared: </p></div><div class="mr-[10%]"><p>{summary["Adj. R-squared"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Method: </p></div><div class="mr-[10%]"><p>{summary["Method"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>F-statistic: </p></div><div class="mr-[10%]"><p>{summary["F-statistic"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Date: </p></div><div class="mr-[10%]"><p>{summary["date"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Prob (F-statistic): </p></div><div class="mr-[10%]"><p>{summary["Prob (F-statistic)"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Time: </p></div><div class="mr-[10%]"><p>{summary["time"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Log-Likelihood: </p></div><div class="mr-[10%]"><p>{summary["Log-Likelihood"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>No. Observations: </p></div><div class="mr-[10%]"><p>{summary["No. Observations"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>AIC: </p></div><div class="mr-[10%]"><p>{summary["AIC"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Df Residuals: </p></div><div class="mr-[10%]"><p>{summary["Df Residuals"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>BIC: </p></div><div class="mr-[10%]"><p>{summary["BIC"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Df Model: </p></div><div class="mr-[10%]"><p>{summary["Df Model"]}</p></div></div>
                    <div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Covariance Type: </p></div><div class="mr-[10%]"><p>{summary["Covariance Type"]}</p></div></div>
                </div>
            </div>
            <div class="flex flex-col items-center">
                <div class="grid grid-cols-2 grid-rows-4 w-[40vw] mt-[10vh] gap-[1vw]">
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Omnibus: </p></div><div class="mr-[10%]"><p>{summary["Omnibus"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Durbin-Watson: </p></div><div class="mr-[10%]"><p>{summary["Durbin-Watson"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Prob(Omnibus): </p></div><div class="mr-[10%]"><p>{summary["Prob(Omnibus)"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Jarque-Bera (JB): </p></div><div class="mr-[10%]"><p>{summary["Jarque-Bera (JB)"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Skew: </p></div><div class="mr-[10%]"><p>{summary["Skew"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Prob(JB): </p></div><div class="mr-[10%]"><p>{summary["Prob(JB)"]}</p></div></div>
                    <div class="data-item shadow-lg h-[5vh] items-center flex justify-between"><div class="ml-[10%]"><p>Kurtosis: </p></div><div class="mr-[10%]"><p>{summary["Kurtosis"]}</p></div></div>
                    <div></div>
                </div>
                <div class="w-[90%] mt-[10vh] grid pr-[20%] items-center">
                    <table>
                        <thead>
                            <tr class="w-full flex">
                                <th class="w-full"></th>
                                <th class="w-full"><p class="text-center mb-[3vh]">Av. Ann. Excess Return</p></th>
                                <th class="w-full"><p class="text-center mb-[3vh]">Return Contribution</p></th>
                            </tr>
                        </thead>
                        <tbody class="grid gap-[5px]">
                            {#each Object.keys(tbl_summary) as rowKey}
                                <tr class="flex w-full gap-[15px] mb-[15px]">
                                    <th class="w-full grid items-center justify-center"><p>{rowKey}</p></th>
                                    {#each Object.keys(tbl_summary[rowKey]) as colKey}
                                        <td class="w-[75%] programming-stats h-[5vh] text-center shadow-xl rounded-lg grid items-center justify-center"><p class="text-lg">{tbl_summary[rowKey][colKey]}</p></td>
                                    {/each}
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
                

            </div>
        </div>

        
    </div>
    {/if}


</body>

<style>

.reg-page{
    grid-template-columns: 15vw 85vw;
}

.programming-stats {
    font-family: 'Rubik', sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    margin: 0 auto;
    /* width: fit-content; */
    box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.3);
    border-radius: 20px;
    padding: 8px 32px;
    color: #023047;
    transition: all 400ms ease;
}
.programming-stats:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 16px -7px rgba(0, 0, 0, 0.3);
}


.data-item{
    transition: all 400ms ease;
}

.data-item:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 16px -7px rgba(0, 0, 0, 0.3);
}
.programming-stats .details ul {
    list-style: none;
    padding: 0;
}

</style>