

<script lang="ts">
    import { onMount } from 'svelte';
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
        Filler,
        ScatterController
    } from 'chart.js';

    import * as Table from "$lib/components/ui/table";

    import Navbar from '../../components/Navbar/+page.svelte';

    import { createEventDispatcher } from 'svelte';
    import Calender from '../../components/Calender/+page.svelte';
    
    let selectedDate = '';
    

    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController);

    let results = {};
    let doughnut_chart;
    let line_chart;
    let combo_chart;

    let isShort = false;
    let isMax = false;
    let isNormal = false;
    let nothing = true;

    let isLoading = false;

    let etflist = []

    let startMonth = '';
    let endMonth = '';
    let startDate = '';
    let endDate = '';
    let constraint = '';



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

        const ctx = document.querySelector('.my-chart').getContext('2d');
        doughnut_chart = new Chart(ctx, {
            
            data: {
                labels: [],
                datasets: [{
                    type: 'doughnut',
                    label: 'Data',
                    data: [],
                }]
            },
            options: {
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

        const lchartx = document.querySelector('.line-chart').getContext('2d');
        line_chart = new Chart(lchartx, {
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

        const cchartx = document.querySelector('.combo-chart').getContext('2d');
        combo_chart = new Chart(cchartx, {
            data: {
                labels: [],
                datasets: [{
                    type: 'line',
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

    function fetchCsv(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(event) {
            const csvData = event.target.result;
            const rows = csvData.split('\n');
            const result = rows.map(row => row.split(',').map(cell => cell.trim()));
            resolve(result);
            };

            reader.onerror = function() {
                reject('Error reading file');
            };

            reader.readAsText(file);
        });
    }

    function handleCheckboxChange2(event) {
        isNormal = event.target.checked;
        
    }
 
 
    let items = [];
    let inputValues = Array(9).fill('');
    let suggestions = Array(9).fill([]);

    function updateSuggestions(index, value) {
        inputValues[index] = value;
        suggestions[index] = etflist
        .filter(ticker => ticker.toLowerCase().includes(value.toLowerCase()))
        .slice(0, 3);
    }


    let isFocused = Array(9).fill(false);

    function handleFocus(index){
        isFocused[index] = true;
    }

    function handleBlur(index){
        isFocused[index] = false;
    }


    function selectSuggestion(index, suggestion) {

        inputValues[index] = suggestion;
        suggestions[index] = [];
    }


    let desStats = [];
    let desStats_labels = ['Mean', 'Std', 'SR'];
    let corrStats = [];

    let robust = [];
    function generateRange(start, end) {
        let range = [];
        for (let i = start; i <= end; i++) {
        range.push(i);
        }
        return range;
    }
    let range = generateRange(1, 100);

    function formatToYYYYMM(dateString) {
        if (!dateString) return '';
        const [year, month] = dateString.split('-');
        return `${year}${month}`;
    }

    const handleSubmit = () => {

        startDate = formatToYYYYMM(startMonth)
        endDate = formatToYYYYMM(endMonth)
        console.log(startDate, endDate)
        for (let value of inputValues) {
            if (value.trim() !== "") {
                items = [...items, value.trim()];
            }
        }
        
        // inputValues = Array(9).fill('');
    };


    function handleStartMonth(event) {
        startMonth = event.detail.monthYear;
    }

    function handleEndMonth(event) {
        endMonth = event.detail.monthYear;
    }

    async function processInput() {
        try {
            isLoading = true;
            await axios.post('http://127.0.0.1:5000/main', {
                ticker_list: items,
                Short: isShort,
                Max: isMax,
                Normal: isNormal,
                Start: Number(`${startDate}`),
                End: Number(`${endDate}`)
            }).then((response ) => {
                isLoading = false;
                return new Promise((resolve, reject) => {
                    nothing = false;
                    resolve(response)
                })
            }).then((response) => {
                results = response.data;
                let allPoints = [];
                results.second_chart.forEach(dataset => {
                    allPoints = allPoints.concat(dataset.data);
                });

                let xValues = allPoints.map(point => point.x);
                let yValues = allPoints.map(point => point.y);

                let minX = Math.min(...xValues);
                let maxX = Math.max(...xValues);
                let minY = Math.min(...yValues);
                let maxY = Math.max(...yValues);

            
                desStats = results.first_prints;
                corrStats = results.second_prints;
                robust = results.third_prints;
                let new_robust = {}

                for(const [key, value] of Object.entries(robust)){
                    if (key !== "Return" && key !== "SR" && key !== "Std"){
                        new_robust[key] = value;
                    }
                    
                }
                constraint = results.constraint;
                console.log(constraint)
                new_robust['Return'] = robust['Return']
                new_robust['Std'] = robust['Std']
                new_robust['SR'] = robust['SR']
                robust = new_robust;
                updateChart(results.first_chart, results.second_chart, minX, maxX, minY, maxY, results.third_chart, results.third_chart_2);
            })
            
        } catch (error) {
            console.log('Error:', error);
        }
        items = []
    }
    function updateChart(dough, fill, minX, maxX, minY, maxY, combo, scatter) {
        const labels = items;
        const dataPoints = dough;
        const comboPoints = combo;
        const colorPalette = [
            "#0072BD", // Blue
            "#D95319", // Orange
            "#EDB120", // Yellow
            "#7E2F8E", // Purple
            "#77AC30", // Green
            "#4DBEEE", // Light Blue
            "#A2142F", // Red
            "#9467BD",
            "#8C564B"
        ];
 
        const stockColorMap = {};

        const getColor = (stock) => {
            if (!stockColorMap[stock]) {
                const availableColors = colorPalette.filter(color => !Object.values(stockColorMap).includes(color));
                stockColorMap[stock] = availableColors.length > 0 ? availableColors[0] : "#000000"; // Default to black if exceeded 9
            }
            return stockColorMap[stock];
        };

        const colors = labels.map(stock => getColor(stock));

        const fillPoints = fill.map((dataset, i) => {
            const color = colors[i];
            return {
                ...dataset,
                backgroundColor: `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 0.5)`,
                borderColor: color,
                fill: true
            };
        });

        // Apply to scatterPoints
        const scatterPoints = scatter.map((dataset, i) => {
            const color = colors[i];
            return {
                ...dataset,
                backgroundColor: i === scatter.length - 1 ? 'red' : color,
                borderColor: i === scatter.length - 1 ? 'red' : color
            };
        });

        const ctx = document.querySelector('.my-chart').getContext('2d');
        const lchartx = document.querySelector('.line-chart').getContext('2d');
        const cchartx = document.querySelector('.combo-chart').getContext('2d');

        
        if (doughnut_chart) {
            doughnut_chart.destroy();
        }
        if (line_chart) {
            line_chart.destroy();
        }
        if (combo_chart) {
            combo_chart.destroy();
        }

        const scatterDataLabels = {
            id: 'scatterDataLabels',

            afterDatasetsDraw(chart, args, options) {
                const {ctx, scales: {x, y}} = chart;
                ctx.save();

                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    if (dataset.type === 'scatter') {
                        dataset.data.forEach((dataPoint, dataIndex) => {

                            const valueX = dataPoint.x;
                            const valueY = dataPoint.y;


                            const pixelX = x.getPixelForValue(valueX);
                            const pixelY = y.getPixelForValue(valueY);

                            ctx.font = '12px sans-serif';
                            ctx.fillText(dataset.label, pixelX, pixelY - 10);
                        });
                    }
                });

            ctx.restore();
            }
        }

        combo_chart = new Chart(cchartx, {
            data: {
                datasets: [...comboPoints.map((points, index) => ({
                    type: 'line',
                    label: `Line ${index + 1}`,
                    data: points,
                    fill: false,
                    borderColor: index === 0 ? 'blue' : 'red',
                    borderWidth: 2,
                    pointRadius: 0
                })),
                ...scatterPoints.map(point => ({
                    type: 'scatter',
                    label: point.label,
                    data: point.data,
                    borderWidth: point.borderWidth,
                    pointRadius: point.pointRadius,
                    backgroundColor: point.backgroundColor,
                    borderColor: point.borderColor
                }))
            ]
            },
            options: {
                responsive: true,
                borderWidth: 10,
                borderRadius: 2,
                hoverBorderWidth: 0,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 20,
                            padding: 10
                        }
                    }
                },
                scales: {
                    y: {
                        type: "linear",
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Expected Returns'
                        }
                    },
                    x: {
                        type: "linear",
                        title: {
                            display: true,
                            text: 'Standard Deviation'
                        }
                    }
                }
            },
            plugins: [scatterDataLabels]
        });

        line_chart = new Chart(lchartx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: fillPoints
               
            },
            options: {
                responsive: true,
                fill: true,
                borderWidth: 10,
                borderRadius: 2,
                hoverBorderWidth: 0,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 20,
                            padding: 10
                        }
                    }
                },
                scales: {
                    y: {
                        type: "linear",
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Allocation'
                        },
                        max: maxY,
                        min: minY
                    },
                    x: {
                        type: "linear",
                        title: {
                            display: true,
                            text: 'Standard Deviation'
                        },
                        max: maxX,
                        min: minX
                    }
                }
            }
        });


        doughnut_chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Data',
                    borderColor: '#2c2e2f',
                    data: dataPoints,
                    backgroundColor: colors
                    
                }]
            },
            options: {
                borderWidth: 2,
                borderRadius: 2,
                hoverBorderWidth: 0,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                        boxWidth: 5,
                        padding: 3
                    }
                }
            }
        }});
    }


</script>

<body class="">

    <Navbar/>
    <div class="main-page" style=" cursor: {isLoading ? 'wait' : 'auto'};">
        
        <div class="all-inputs">
            <div>
                <h2 class="mb-[3vh] text-xl">Advanced Options</h2>
                <div class="checks text-lg mb-[5vh]">
                    <div class="flex flex-row gap-[1vw] justify-center align-center">
                        <label><input class="w-[2.5vh] h-[2.5vh]  rounded hover:border-[#5ce07f]" type="checkbox" name="btn" on:change={handleCheckboxChange2} checked={isNormal}></label>
                        <h2>Normal</h2>
                        <div class="hover-container">
                            <i class="fa-solid fa-circle-question items-middle" style="color: #5ce07f;"></i>
                            <div class="hover-textbox">
                                Lorem ipsum odor amet, consectetuer adipiscing elit. Non quam inceptos natoque sem phasellus, ex euismod consequat luctus.
                            </div>
                        </div>
                    </div>
                </div>
                
            </div>
            <div class="dates mb-[5vh]">
                <h2 class="text-xl mb-[3vh]">Picking Dates (Start Yr/Month. End Yr/Month)</h2>
                <div class="grid grid-cols-2 w-[75%] gap-[2vw]">
                      <Calender bind:selectedMonthYear={startMonth} on:monthSelected={handleStartMonth} />
                      <Calender bind:selectedMonthYear={endMonth} on:monthSelected={handleEndMonth} />
                </div>
            </div>
            <div class="tickers mb-[5vh]">
                <h2 class="text-xl mb-[3vh]">Ticker Symbols</h2>
                <div class="grid grid-rows-3 grid-cols-3 gap-[2vh] w-[75%]">
            
                    {#each inputValues as inputValue, index}
                        <div class="relative">
                        <input
                            class="w-full h-[5vh] p-[10px] border-2 border-[#A9A9A9] hover:border-[#5ce07f] rounded-md outline-none"
                            type="text"
                            placeholder="Place ticker here..."
                            bind:value={inputValues[index]}
                            on:input={(e) => updateSuggestions(index, e.target.value)}
                            on:focus={() => handleFocus(index)}
                            on:blur={() => setTimeout(() => handleBlur(index), 500)}
                        >
                        {#if isFocused[index] && suggestions[index].length > 0}
                            <ul class="absolute bg-[#2c2e2f] border border-gray-300 w-full mt-1 rounded-md z-10 outline-none">
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
            <button class="py-[10px] px-[30px] text-xl border-[#A9A9A9] rounded-md ease-in-out duration-150 border-2 text-black border-[#5ce07f] bg-[#5ce07f] hover:bg-[#282828] hover:text-[#5ce07f] hover:border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>
            
        </div>
        <div class="flex flex-col h-full items-center justify-center">
            <h1 class="text-2xl mb-[5vh]">Optimal Mean-Variance Weights</h1>
            <div class="programming-stats">
                {#if nothing}
                    <p>Enter your desired portfolio</p>
                {/if}
                {#if !nothing}
                <canvas class="w-[50vh] my-chart"></canvas>
                {/if}
            </div>
            <p class="text-[#8c8c8c] text-sm mt-[1vh]">{constraint}</p>
            
        </div>
    </div>
    {#if !nothing}
    <div class="lgraph w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-xl mb-[5vh] text-center">Efficient Frontier Transition Map</h1>
        <div class="programming-stats max-h-[70vh] w-[70vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[55vw] min-w-[400px] line-chart"></canvas>
        </div>
        <p class="text-[#8c8c8c] text-sm mt-[1vh] text-center">{constraint}</p>
    </div>
    <div class="bg-white w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-xl mb-[5vh] text-center">Efficient Frontier</h1>
        <div class="programming-stats max-h-[70vh] w-[70vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[55vw] min-w-[400px] combo-chart"></canvas>
        </div>
        <p class="text-[#8c8c8c] text-sm mt-[1vh] text-center">{constraint}</p>
    </div>
    <div class=" w-[100vw] pt-[15vh]">
        <div class="grid grid-cols-2 gap-[5vw] w-[90vw] justify-self-center justify-center align-center">
        
            <div>
                <h1 class="text-center text-xl mb-[5vh]">Asset Descriptive Statistics</h1>
                <ul class="grid grid-cols-3 gap-[1.4vw]">
                    {#each desStats as item}
    
                    <li class="flex flex-col justify-self-center rounded-xl items-start p-[2vh] w-[10vw] gap-[2vh] border-2 border-[#262629] shadow-lg">
                        {#each Object.entries(item) as [key, values]}
                            <h1 class="w-full border-b border-gray-700 py-4 text-xl text-start">{key}</h1>
                            <div class="flex flex-col w-full">
                                {#each values as value, index}
                                    <div class="text-sm grid grid-cols-2  mb-[2vh]">
                                        <p>{desStats_labels[index]}</p>
                                        <p class="text-end">{value}</p>
                                    </div>
                                {/each}
                            </div>
                        {/each}
                    </li>
                    {/each}
                </ul>
            </div>
            <div>
                <h1 class="text-center text-xl mb-[5vh]">Asset Correlation Matrix</h1>
                
                <table class="w-[100%] border-collapse border border-gray-300">
                    <thead>
                      <tr class="bg-[#949494]">
                        <th class="border border-gray-300 p-3 text-center font-bold"> </th>
                        {#each Object.keys(corrStats) as key}
                          <th class="border border-gray-300 p-3 text-center font-bold">{key}</th>
                        {/each}
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.keys(corrStats) as rowKey}
                        <tr>
                          <th class="border bg-[#949494] border-gray-300 p-3 text-center font-medium">{rowKey}</th>
                          {#each Object.keys(corrStats[rowKey]) as colKey}
                            <td class="border border-gray-300 text-center p-3 hover:bg-[#2b2c30] transition-all ease-in-out duration-200">
                              <p class="text-base font-mono">{corrStats[rowKey][colKey].toFixed(2)}</p>
                            </td>
                          {/each}
                        </tr>
                      {/each}
                    </tbody>
                  </table>
            </div>
            
        </div>
        <div class="w-full flex flex-col justify-center items-center">
            <h1 class="text-center text-xl mt-[5vh] mb-[5vh]">Robust Efficient Frontier Portfolios</h1>
            <div class="w-[80vw]">
                <Table.Root shadow>
                    <Table.Header>
                        <Table.Head>Index</Table.Head>
                        {#each Object.keys(robust) as key}
                            <Table.Head>{key}</Table.Head>
                        {/each}
                    </Table.Header>
                    <Table.Body tableBodyClass="divide-y  max-h-[40vh]">
                        {#each range as num}
                        <Table.Row>
                            <Table.Cell>{num}</Table.Cell>
                            {#each Object.keys(robust) as key}
                                <Table.Cell>{robust[key][num]}</Table.Cell>
                            {/each}
                        </Table.Row>
                        {/each}
                        
                    </Table.Body>
                </Table.Root>
            </div>
            
        </div>
    </div>
    
    
    {/if}
</body>


<style lang="css">
    @import 'flowbite';

    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap');
    @import '../../app.css';

    .date-picker {
    position: relative;
    display: inline-block;
  }

  .btn {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 4px;
  }

  .calendar {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 1000;
    background-color: white;
    border: 1px solid #ccc;
    padding: 10px;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
  }

  input[type="date"] {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
    .hover-container {
        position: relative;
        display: inline-block;
    }

    .hover-textbox {
        visibility: hidden;
        background-color: #555;
        color: #fff;
        text-align: center;
        width: 10vw;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        font-size: 14px;
        line-height: 2vh;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .hover-container:hover .hover-textbox {
        visibility: visible;
        opacity: 1;
    }

    select:focus{
        outline: none;
    }
    input:focus{
        outline: none !important;
    }
    .main-page{
        width: 100vw;
        height: 100vh;
        display: grid;
        grid-template-columns: 1fr 1fr;  
        align-items: center;
        position: relative;
        top: 0;
        left: 0;

    }

    .all-inputs{
        margin-left: 12vw;
        
    }

    .checks{
        display: flex;
        flex-direction: row;
        gap: 5vw;
    }

    .checks h2{
        text-align: center;
    }


    .chart-heading {
        font-family: 'Rubik', sans-serif;
        color: white;
        text-transform: uppercase;
        font-size: 24px;
        text-align: center;
    }

    .programming-stats {
        font-family: 'Rubik', sans-serif;
        display: flex;
        justify-content: end;
        gap: 24px;
        margin: 0 auto;
        box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.3);
        border-radius: 20px;
        padding: 8px 32px;
        color: black;
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
    
    
</style>