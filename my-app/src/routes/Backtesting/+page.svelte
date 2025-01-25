<script lang="ts">
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

    import * as Table from "$lib/components/ui/table";

    import CalendarIcon from "lucide-svelte/icons/calendar";
    import {
        type DateValue,
        DateFormatter,
        getLocalTimeZone,
    } from "@internationalized/date";
    import { cn } from "$lib/utils.js";
    import { Button } from "$lib/components/ui/button";
    import { Calendar } from "$lib/components/ui/calendar";
    import * as Popover from "$lib/components/ui/popover";
    
    const df = new DateFormatter("en-US", {
        dateStyle: "long",
    });
    
    let value: DateValue | undefined = undefined;


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

        }else{ 
            const response = await fetchCsv('/ETF_tickers_only.csv');
            etflist = response;

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
        .filter(ticker => ticker.toLowerCase().startsWith(value.toLowerCase()))
        .slice(0, 3);
    }

    function selectSuggestion(index, suggestion) {
        inputValues[index] = suggestion;
        suggestions[index] = [];
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
    <div class=" pt-[10vh] h-[25vh] text-black flex  justify-center gap-[2vw]">
        <div class=" col-span-2 flex flex-col justify-end items-center">
            <h2 class="text-lg mb-[3vh] px-[1vw]">Picking Dates (Start Yr/Month. End Yr/Month)</h2>
            <div class="flex gap-[2vw]">
            <Popover.Root>
                <Popover.Trigger asChild let:builder>
                  <Button
                    variant="outline"
                    class={cn(
                      "w-[240px] justify-start text-left font-normal",
                      !value && "text-muted-foreground"
                    )}
                    builders={[builder]}
                  >
                    <CalendarIcon class="mr-2 h-4 w-4" />
                    {value ? df.format(value.toDate(getLocalTimeZone())) : "Pick a date"}
                  </Button>
                </Popover.Trigger>
                <Popover.Content class="w-auto p-0" align="start">
                  <Calendar bind:value />
                </Popover.Content>
              </Popover.Root>
              <Popover.Root>
                <Popover.Trigger asChild let:builder>
                  <Button
                    variant="outline"
                    class={cn(
                      "w-[240px] justify-start text-left font-normal",
                      !value && "text-muted-foreground"
                    )}
                    builders={[builder]}
                  >
                    <CalendarIcon class="mr-2 h-4 w-4" />
                    {value ? df.format(value.toDate(getLocalTimeZone())) : "Pick a date"}
                  </Button>
                </Popover.Trigger>
                <Popover.Content class="w-auto p-0" align="start">
                  <Calendar bind:value />
                </Popover.Content>
              </Popover.Root>
            </div>
            <!-- <div class="grid grid-cols-4 w-full gap-[1vw]">
                <select class=" border-2 flex justify-center items-center rounded h-[4vh] hover:border-[#5ce07f] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={startYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded h-[4vh] hover:border-[#5ce07f] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={startMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
                
                <select class="border-2 flex justify-center items-center rounded h-[4vh] hover:border-[#5ce07f] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={endYear}>
                    {#each years as year}
                    <option class="text-sm rounded" value={year}>{year}</option>
                    {/each}
                </select>
                <select class="border-2 flex justify-center items-center rounded h-[4vh] hover:border-[#5ce07f] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={endMonth}>
                    {#each Object.entries(months) as [month, value]}
                    <option class="text-sm rounded" value={month}>{month}</option>
                    {/each}
                </select>
            </div> -->
        </div>
        <div class="flex flex-col justify-end items-center">
            <h2 class="text-lg mb-[3vh]">Rebalancing</h2>
            <select class="border-2  flex justify-center items-center rounded h-[4vh] hover:border-[#5ce07f] border-[#696a6b] text-base pl-[2%]" id="balance-picker" bind:value={rebalance}>
                {#each balances as balance}
                <option class="text-sm rounded" value={balance}>{balance}</option>
                {/each}
            </select>
        </div>
        <div class="flex flex-col justify-end items-center w-[7vw]">
            <h2 class="text-lg mb-[3vh]">Start Balance</h2>
            <input class="border-2 flex justify-center items-center w-[90%] rounded  hover:border-[#5ce07f] h-[4vh] text-sm border-[#696a6b]  pl-[5%]" type='number' bind:value={startBalance} placeholder="Enter numbers only">

        </div>
        <div class="flex flex-col justify-end items-center w-[7vw]">
            <h2 class="text-lg mb-[3vh]">Benchmark</h2>
            <input class="border-2 flex justify-center items-center rounded w-[90%] hover:border-[#5ce07f] h-[4vh] border-[#696a6b] text-sm pl-[5%]" type='text' bind:value={benchmark} placeholder="Enter benchmark">

        </div>
        <div class="flex flex-col justify-end items-end">
            <button class="py-[10px] px-[30px] text-black text-xl rounded-md border-[#5ce07f] bg-[#5ce07f] ease-in-out duration-150 border-2 hover:bg-[#282828] hover:text-[#C0C0C0] hover:border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>

        </div>

    </div>
    <div class="flex text-black">
        <div class="w-[40%] h-[75vh] flex flex-col justify-center">
            <div class="tickers mb-[3vh] pl-[25%]">
                <h2 class="text-lg mb-[1vh] w-full">Ticker Symbols</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[1.5vh] ">
            
                    {#each inputValues as inputValue, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] hover:border-[#5ce07f] border-2 text-sm border-[#696a6b]  rounded-md outline-none"
                            type="text"
                            placeholder="Place ticker..."
                            bind:value={inputValues[index]}
                            on:input={(e) => updateSuggestions(index, e.target.value)}
                            on:focus={() => handleFocus(index)}
                            on:blur={() => setTimeout(() => handleBlur(index), 150)}
                        >
                        {#if isFocused[index] && suggestions[index].length > 0}
                            <ul class="absolute bg-[#2c2e2f] border border-gray-300 w-full mt-1 border-[#5ce07f] rounded-md z-10 outline-none">
                            {#each suggestions[index] as suggestion}
                                <option class="p-2 rounded-md hover:bg-[#131217] cursor-pointer"  on:click={() => selectSuggestion(index, suggestion)}>
                                {suggestion}
                                </option>
                            {/each}
                            </ul>
                        {/if}
                        </div>
                    {/each}
    
                </div>
                
            </div>
            <div class="tickers mb-[3vh] pl-[25%]">
                <h2 class="text-lg mb-[1vh]">Allocation 1</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh]">
            
                    {#each allocations1 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] border-2 hover:border-[#5ce07f] text-sm border-[#696a6b]  rounded-md outline-none"
                            type="number"
                            placeholder="number"
                            bind:value={allocations1[index]}
                        >
                        
                        </div>
                    {/each}
    
                </div>
            </div>
            <div class="tickers mb-[3vh] pl-[25%]">
                <h2 class="text-lg mb-[1vh]">Allocation 2</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh]">
            
                    {#each allocations2 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] text-sm hover:border-[#5ce07f] border-2 border-[#696a6b]  rounded-md outline-none"
                            type="number"
                            placeholder="number"
                            bind:value={allocations2[index]}
                        >
                        
                        </div>
                    {/each}
    
                </div>
            </div>
            <div class="tickers mb-[3vh] pl-[25%]">
                <h2 class="text-lg mb-[1vh]">Allocation 3</h2>
                <div class="grid grid-rows-2 grid-cols-5 gap-[2vh]">
            
                    {#each allocations3 as allocation_value, index}
                        <div class="relative">
                        <input
                            class="w-full h-[4vh] p-[10px] text-sm border-2 hover:border-[#5ce07f] border-[#696a6b] rounded-md outline-none"
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
        <div class="w-[60%] pl-[2vw] h-[75vh] flex flex-col justify-center align-center">
            <h1 class="text-xl mb-[5vh] text-center">Portfolio Growths</h1>
            <div class="programming-stats max-h-[65vh] w-[55vw] min-w-[400px]">
                <canvas class="w-[45vw] min-w-[400px] growth-chart"></canvas>
            </div>
        </div>
        {/if}
    </div>
    {#if !nothing}
        <div class="w-full h-[100vh] border-t-[#313131] bg-[#1c1c1c] flex flex-col border-t-[5px] justify-center align-center">
            <h1 class="text-xl mb-[5vh] text-[#C0C0C0] text-center">Annual Returns</h1>
            <div class="programming-stats max-h-[80vh] w-[60vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[55vw] min-w-[400px] annual-returns-chart"></canvas>
            </div>
        </div>
        <div class="w-full h-[100vh] text-[#C0C0C0] bg-[#1c1c1c] flex flex-col justify-center align-center">
            <h1 class="text-xl mb-[5vh] text-center">Drawdown Data</h1>
            <div class="programming-stats max-h-[80vh] w-[60vw] min-w-[400px] p-[5vh]">
                <canvas class="w-[55vw] min-w-[400px] drawdown-chart"></canvas>
            </div>
        </div>
    {/if}
    {#if port_allocations}
    <div class="bg-[#1c1c1c] text-[#C0C0C0]">
        <h1 class="text-xl mb-[5vh] text-center">Portfolio Allocation</h1>
        <div class="w-[70%] h-[30vh] grid grid-cols-3 justify-self-center ">
            {#each Object.keys(port_allocations) as i}
                <div class="flex flex-col justify-self-center rounded-xl items-start p-[2vh] w-[15vw] gap-[2vh] border-2 border-[#262629] shadow-lg bg-[#1c1c1f]">
                    <h1 class="w-full border-b border-gray-700 py-4 text-xl">{i}</h1>
                    <div class="flex flex-col">
                        {#each Object.keys(port_allocations[i]) as j}
                        <div class=" text-sm grid grid-cols-2 gap-[5vw] mb-[2vh]">
                            <p>{j}</p>
                            <p>{port_allocations[i][j]}</p>
                        </div>
                        {/each}
                    </div>
                </div>
                
            {/each}
        </div>
       
    
        <h1 class="text-xl mb-[5vh] mt-[10vh] text-center">Top 3 Drawdowns</h1>
        <div class="w-[70%] justify-self-center">
            {#each Object.keys(drawdown_print) as d}
            <Table.Root class="rounded-lg mb-[5vh]">
                <Table.Caption>Top 3 drawdowns {d}</Table.Caption>
                <Table.Header>
                    {#each Object.keys(drawdown_print[d]) as k}
                        <Table.Head>{k}</Table.Head>
                    {/each}
                </Table.Header>
                <Table.Body>
                    {#each Array.from({ length: drawdown_print[d]['Rank'].length }) as _, i}
                    <Table.Row>
                        {#each Object.keys(drawdown_print[d]) as j}
                            <Table.Cell>{drawdown_print[d][j][i]}</Table.Cell>
                        {/each}
                    </Table.Row>
                    {/each}
                </Table.Body>
            </Table.Root>
            {/each}
        </div>
        <h1 class="text-xl mb-[5vh] mt-[10vh] text-center">Regression Analysis</h1>
        <div class="w-[70%] justify-self-center">
            {#each Object.keys(regression_analysis) as category}
                <!-- <h2 class="text-lg font-semibold mt-4 text-center">Regression Analysis {category}</h2>
                <div class="grid grid-cols-4">
                    <h2>R Square: {regression_analysis[category]["R-squared"]}</h2>
                    <h2>Adjusted R Square: {regression_analysis[category]["Adjusted R-squared"]}</h2>
                    <h2>Observations: {regression_analysis[category]["Observations"]}</h2>
                    <h2>Annualized Alpha: {regression_analysis[category]["Annualized alpha"].toFixed(6)}</h2>
                </div> -->
                <Table.Root class="mb-[5vh]">
                    <Table.Caption>Regression Analysis {category} | R Square: {regression_analysis[category]["R-squared"]} | Adjusted R Square: {regression_analysis[category]["Adjusted R-squared"]} | Observations: {regression_analysis[category]["Observations"]} | Annualized Alpha: {regression_analysis[category]["Annualized alpha"].toFixed(6)}</Table.Caption>
                    <Table.Header>
                        <Table.Head></Table.Head>
                        {#each metrics as metric}
                            <Table.Head>{metric}</Table.Head>
                        {/each}
                    
                    </Table.Header>
                    <Table.Body>
                        {#each ['alpha', 'beta'] as subcategory}
                            <Table.Row>
                                <Table.Cell class="font-semibold">{subcategory}</Table.Cell>
                                {#each metrics as metric}
                                    <Table.Cell>{regression_analysis[category][subcategory][metric].toFixed(6)}</Table.Cell>
                                {/each}
                            </Table.Row>
                        {/each}
                    </Table.Body>
                </Table.Root>
            {/each}
        </div>
    </div>
    
   
    
    {/if}


    
    

</body>

<style>
@import '../../app.css';
.programming-stats {
    font-family: 'Rubik', sans-serif;
    display: flex;
    align-items: center;
    gap: 24px;
    margin: 0 auto;
    /* width: fit-content; */
    /* box-shadow: 0 4px 12px -2px rgba(255, 255, 255, .3); */
    border-radius: 20px;
    border-width: 2px;
    border-color: #2b3135;
    padding: 8px 32px;
    transition: all 400ms ease;
    /* background-color: #2e3233; */
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