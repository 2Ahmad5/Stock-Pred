<script>
    import { onMount } from "svelte";
    import Navbar from "../../Navbar/+page.svelte";
    import axios from 'axios';
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
        TimeScale,
        Filler,
        ScatterController,
        BarController,
        BarElement,
    } from 'chart.js';
    import 'chartjs-adapter-date-fns';

    import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell } from 'flowbite-svelte';


    Chart.register(BarController, BarElement, DoughnutController, TimeScale, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController);

    let growthChart;
    let anreturnsChart;
    let drawdownChart;
    let port_allocations;
    let drawdown_print;
    let regression_analysis;
    let metrics;

    let nothing = true;


    let startYear = '';
    let endYear = '';
    let startMonth = '';
    let endMonth = '';
    let rebalance = '';
    let benchmark = '';
    /** @type {number} */
    let startBalance;



    let years = [];
    let balances = ['daily', 'weekly', 'monthly', 'yearly']
    /**@type {string[]}*/
    let benchmarks = []
    let csvData = []
    /**@type {string[]}*/
    let etflist = []
    let isFocused = Array(10).fill(false);
    const desiredOrder = [
    "Rank", 
    "Start date", 
    "End date", 
    "Length", 
    "Recovered by", 
    "Recovery time", 
    "Underwater period", 
    "Drawdown"
    ];

    
    /**
     * @type {number[]}
     */
    let allocations1 = Array(10).fill(null);
    let allocations2 = Array(10).fill(null);
    let allocations3 = Array(10).fill(null);
    /**@type {string[]}*/
    let items = [];
    let inputValues = Array(10).fill('');
    let suggestions = Array(10).fill([]);


    let months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    let results = {}


    for (let year = 1970; year <= 2024; year++) {
        years.push(year);
    }

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

        const gchartx = document.querySelector('.growth-chart').getContext('2d');
        const achartx = document.querySelector('.annual-returns-chart').getContext('2d');
        const dchartx = document.querySelector('.drawdown-chart').getContext('2d');

        growthChart = new Chart(gchartx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Data',
                    data: [],
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });

        anreturnsChart = new Chart(achartx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Data',
                    data: [],
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });

        drawdownChart = new Chart(dchartx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Data',
                    data: [],
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        })

    });

    /**
     * @param {Blob} file
     */
    function fetchCsv(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(event) {
            
            const csvData = event.target ? event.target.result  : '';
            /**@type {string}*/
            const rows = csvData ? csvData.split('\n') : '';
            
            const result = rows.map((/** @type {string} */ row) => row.split(',').map(cell => cell.trim()));
            resolve(result);
            };

            reader.onerror = function() {
                reject('Error reading file');
            };

            reader.readAsText(file);
        });
    }

    function handleFocus(index){
        isFocused[index] = true;
    }

    function handleBlur(index){
        isFocused[index] = false;
    }

    /**
     * @param {number} index
     * @param {string} value
     */
    function updateSuggestions(index, value) {
        inputValues[index] = value;
        suggestions[index] = etflist
        .filter(ticker => ticker.toLowerCase().includes(value.toLowerCase()))
        .slice(0, 3);
    }

    const handleSubmit = () => {
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
        items = inputValues


        console.log(allocations1)

        benchmarks.push(benchmark);
        
        inputValues = Array(10).fill('');
        nothing = false;
    }

    async function processInput() {
        try{
            await axios.post('http://127.0.0.1:5000/regres', {

                ticker_list: items,
                start: Number(`${startYear}${startMonth}`),
                end: Number(`${endYear}${endMonth}`),
                benchmark: benchmarks,
                allocation1: allocations1,
                allocation2: allocations2,
                allocation3: allocations3,
                startBalance: startBalance,
                rebalance: rebalance

            }).then((response) => {
                return new Promise((resolve, reject) => {
                    resolve(response)
                })
            }).then((response) => {
                results = response.data
                
                console.log(results)
                // console.log(nothing)
                port_allocations = results.port_allocations
                drawdown_print = {};
                for (const key in results.drawdown_print) {
                    const portfolioData = results.drawdown_print[key];
                    drawdown_print[key] = {};

                    desiredOrder.forEach(column => {
                        if (portfolioData[column]) {
                            drawdown_print[key][column] = portfolioData[column];
                        }
                    });
                }
                regression_analysis = results.regression_analysis
                metrics = metrics = Object.keys(regression_analysis[Object.keys(regression_analysis)[0]].alpha);
                console.log(port_allocations)
                console.log(drawdown_print)
                console.log(regression_analysis)
                nothing = false;
                updateChart(results.portfolio_growths, results.annual_returns_data, results.drawdown_data)

            })
        } catch (error) {
            console.error('Error:', error);
        }
        items = []
        allocations1 = Array(10).fill(null);
        allocations2 = Array(10).fill(null);
        allocations3 = Array(10).fill(null);
        benchmarks = []

    }

    function updateChart(portfolio_growths, annual_returns_data, drawdown_chart) {


        const gchartx = document.querySelector('.growth-chart').getContext('2d');
        const achartx = document.querySelector('.annual-returns-chart').getContext('2d');
        const dchartx = document.querySelector('.drawdown-chart').getContext('2d');

        if(growthChart){
            growthChart.destroy();
        }
        if(anreturnsChart){
            anreturnsChart.destroy();
        }
        if(drawdownChart){
            drawdownChart.destroy();
        }
        

        const labels = portfolio_growths[Object.keys(portfolio_growths)[0]][0]; // Use x-values from the first portfolio for labels

        const gdatasets = Object.keys(portfolio_growths).map((portfolio, index) => {
            const xValues = portfolio_growths[portfolio][0]; // Dates or x-values
            const yValues = portfolio_growths[portfolio][1]; // Growth or y-values

            return {
                label: portfolio,
                data: yValues,
                backgroundColor: `rgba(${100 + index * 30}, ${150 - index * 20}, ${200 + index * 20}, 0.6)`,
                borderColor: `rgba(${100 + index * 30}, ${150 - index * 20}, ${200 + index * 20}, 1)`,
                borderWidth: 1
            };
        });

        growthChart = new Chart(gchartx, {
            type: 'line',
            data: {
                labels: labels, 
                datasets: gdatasets 
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'year',
                            displayFormats: {
                                year: 'yyyy'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        type: 'linear'
                    }
                }
            }
        });

        anreturnsChart = new Chart(achartx, {
            type: 'bar',
            data: {
                labels: annual_returns_data['labels'].map(year => `${year}-01-01`),
                datasets: annual_returns_data['datasets'],
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'year',
                            displayFormats: {
                                year: 'yyyy'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        type: 'linear',
                        
                    }
                }
            }
        });

        const ddatasets = Object.keys(drawdown_chart['portfolios']).map((portfolio, index) => {
            const yValues = drawdown_chart['portfolios'][portfolio]; // Growth or y-values

            return {
                label: portfolio,
                data: yValues,
                backgroundColor: `rgba(${100 + index * 30}, ${150 - index * 20}, ${200 + index * 20}, 0.6)`,
                borderColor: `rgba(${100 + index * 30}, ${150 - index * 20}, ${200 + index * 20}, 1)`,
                borderWidth: 1
            };
        });

        drawdownChart = new Chart(dchartx, {
            type: 'line',
            data: {
                labels: drawdown_chart['dates'],
                datasets: ddatasets
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'year',
                            displayFormats: {
                                year: 'yyyy'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        type: 'linear'
                    }
                }
            }
        });
        
        
        



    }

</script>

<body>
    <Navbar/>
    <div class="w-[100vw] pt-[10vh] h-[25vh] bg-[#5ce07f] grid grid-cols-6">
        <div class="col-span-2 flex flex-col justify-center items-center">
            <h2 class="text-2xl mb-[3vh]">Picking Dates (Start Yr/Month. End Yr/Month)</h2>
            <div class="grid grid-cols-4 w-[90%] gap-[2vw]">
                <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={startYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={startMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
                
                <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={endYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="year-picker" bind:value={endMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
            </div>
        </div>
        <div class="flex flex-col justify-center items-center">
            <h2 class="text-2xl mb-[3vh]">Rebalancing</h2>
            <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl pl-[5%]" id="balance-picker" bind:value={rebalance}>
                {#each balances as balance}
                <option class="text-sm rounded" value={balance}>{balance}</option>
                {/each}
            </select>
        </div>
        <div class="flex flex-col justify-center items-center">
            <h2 class="text-2xl mb-[3vh]">Start Balance</h2>
            <input class="border-2 flex justify-center items-center rounded w-[50%] h-[4vh] border-[#696a6b] text-xl pl-[2%]" type='number' bind:value={startBalance} placeholder="Enter numbers only">

        </div>
        <div class="flex flex-col justify-center items-center">
            <h2 class="text-2xl mb-[3vh]">Benchmark</h2>
            <input class="border-2 flex justify-center items-center rounded w-[50%] h-[4vh] border-[#696a6b] text-xl pl-[2%]" type='text' bind:value={benchmark} placeholder="Enter benchmark">

        </div>
        <div class="flex flex-col justify-center items-center">
            <button class="py-[10px] px-[30px] text-xl rounded-md bg-white ease-in-out duration-150 border-2 border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>

        </div>

    </div>
    <div class="flex">
        <div class="w-[30%] h-[75vh] bg-[#5ce07f] flex flex-col items-center justify-center pl-[2vw]">
            <div class="tickers mb-[3vh]">
                <h2 class="text-2xl mb-[1vh]">Ticker Symbols</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh] w-[95%]">
            
                    {#each inputValues as inputValue, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
                            type="text"
                            placeholder="Place ticker here..."
                            bind:value={inputValues[index]}
                            on:input={(e) => updateSuggestions(index, e.target.value)}
                            on:focus={() => handleFocus(index)}
                            on:blur={() => setTimeout(() => handleBlur(index), 500)}
                        >
                        {#if isFocused[index] && suggestions[index].length > 0}
                            <ul class="absolute bg-white border border-gray-300 w-full mt-1 rounded-md z-10 outline-none">
                            {#each suggestions[index] as suggestion}
                                <option class="p-2 hover:bg-gray-200 cursor-pointer"  on:click={() => selectSuggestion(index, suggestion)}>
                                {suggestion}
                                </option>
                            {/each}
                            </ul>
                        {/if}
                        </div>
                    {/each}
    
                </div>
                
            </div>
            <div class="tickers mb-[3vh]">
                <h2 class="text-2xl mb-[1vh]">Allocation 1</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh] w-[95%]">
            
                    {#each allocations1 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
                            type="number"
                            placeholder="number"
                            bind:value={allocations1[index]}
                        >
                        
                        </div>
                    {/each}
    
                </div>
            </div>
            <div class="tickers mb-[3vh]">
                <h2 class="text-2xl mb-[1vh]">Allocation 2</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh] w-[95%]">
            
                    {#each allocations2 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
                            type="number"
                            placeholder="number"
                            bind:value={allocations2[index]}
                        >
                        
                        </div>
                    {/each}
    
                </div>
            </div>
            <div class="tickers mb-[3vh]">
                <h2 class="text-2xl mb-[1vh]">Allocation 3</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh] w-[95%]">
            
                    {#each allocations3 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
                            type="number"
                            placeholder="number"
                            bind:value={allocations3[index]}
                        >
                        
                        </div>
                    {/each}
    
                </div>
            </div>
    
        </div>
        {#if !nothing}
        <div class="w-[70%] pl-[2vw] h-[75vh] justify-center align-center">
            <h1 class="text-4xl mb-[5vh] text-center">Portfolio Growths</h1>
            <div class="programming-stats max-h-[65vh] w-[65vw] min-w-[400px]">
                <canvas class="w-[65vw] min-w-[400px] growth-chart"></canvas>
            </div>
        </div>
        {/if}
    </div>
    {#if !nothing}
        <div class="w-full h-[100vh] justify-center align-center">
            <h1 class="text-4xl mb-[5vh] text-center">Annual Returns</h1>
            <div class="programming-stats max-h-[80vh] w-[80vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[75vw] min-w-[400px] annual-returns-chart"></canvas>
            </div>
        </div>
        <div class="w-full h-[100vh] justify-center align-center">
            <h1 class="text-4xl mb-[5vh] text-center">Drawdown Data</h1>
            <div class="programming-stats max-h-[80vh] w-[80vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[75vw] min-w-[400px] drawdown-chart"></canvas>
            </div>
        </div>
    {/if}
    {#if port_allocations}
    <h1 class="text-4xl mb-[5vh] text-center">Portfolio Allocation</h1>
    <div class="w-[70%] h-[30vh] grid grid-cols-3 justify-self-center ">
        {#each Object.keys(port_allocations) as i}
            <div class="flex flex-col justify-center">
                <h1 class="text-2xl mb-[4vh]">{i}</h1>
                <div class="flex flex-col">
                    {#each Object.keys(port_allocations[i]) as j}
                    <div class="flex gap-[5vw] mb-[2vh]">
                        <p>{j}</p>
                        <p>{port_allocations[i][j]}</p>
                    </div>
                    {/each}
                </div>
            </div>
        {/each}
    </div>

    <h1 class="text-4xl mb-[5vh] text-center">Top 3 Drawdowns</h1>
    <div class="w-[70%] justify-self-center">
        {#each Object.keys(drawdown_print) as d}
        <h2 class="mb-[2vh] mt-[4vh] font-bold text-center">Top 3 drawdowns {d}</h2>
        <Table noborder={true} class="rounded-lg">
            <TableHead>
                {#each Object.keys(drawdown_print[d]) as k}
                    <TableHeadCell>{k}</TableHeadCell>
                {/each}
            </TableHead>
            <TableBody>
                {#each Array.from({ length: drawdown_print[d]['Rank'].length }) as _, i}
                <TableBodyRow>
                    {#each Object.keys(drawdown_print[d]) as j}
                        <TableBodyCell>{drawdown_print[d][j][i]}</TableBodyCell>
                    {/each}
                </TableBodyRow>
                {/each}
            </TableBody>
        </Table>
        {/each}
    </div>

    <h1 class="text-4xl mb-[5vh] mt-[10vh] text-center">Regression Analysis</h1>
    <div class="w-[70%] justify-self-center">
        {#each Object.keys(regression_analysis) as category}
            <h2 class="text-lg font-semibold mt-4 text-center">Regression Analysis {category}</h2>
            <div class="grid grid-cols-4">
                <h2>R Square: {regression_analysis[category]["R-squared"]}</h2>
                <h2>Adjusted R Square: {regression_analysis[category]["Adjusted R-squared"]}</h2>
                <h2>Observations: {regression_analysis[category]["Observations"]}</h2>
                <h2>Annualized Alpha: {regression_analysis[category]["Annualized alpha"].toFixed(6)}</h2>
            </div>
            <Table noborder={true}>
                <TableHead >
                    <TableHeadCell></TableHeadCell>
                    {#each metrics as metric}
                        <TableHeadCell>{metric}</TableHeadCell>
                    {/each}
                
                </TableHead>
                <TableBody>
                    {#each ['alpha', 'beta'] as subcategory}
                        <TableBodyRow>
                            <TableBodyCell class="font-semibold">{subcategory}</TableBodyCell>
                            {#each metrics as metric}
                                <!-- Use .toFixed(6) to round to 6 decimal places -->
                                <TableBodyCell>{regression_analysis[category][subcategory][metric].toFixed(6)}</TableBodyCell>
                            {/each}
                        </TableBodyRow>
                    {/each}
                </TableBody>
            </Table>
        {/each}
    </div>
   
    
    {/if}


    
    

</body>

<style>

.programming-stats {
    font-family: 'Rubik', sans-serif;
    display: flex;
    align-items: center;
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
.programming-stats .details ul {
    list-style: none;
    padding: 0;
}

</style>