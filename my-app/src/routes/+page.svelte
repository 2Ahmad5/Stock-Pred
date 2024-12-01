<script>
    //@ts-ignore
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

    import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell } from 'flowbite-svelte';

    import Navbar from '../Navbar/+page.svelte';

    
    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController);

    // @ts-ignore
    let userInput = '';
    let results = {};
    // @ts-ignore
    let doughnut_chart;
    let line_chart;
    let combo_chart;

    let isShort = false;
    let isMax = false;
    let isNormal = false;
    let nothing = true;

    let isLoading = false;

    let csvData = []
    let etflist = []

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


    // @ts-ignore
    // @ts-ignore
    function handleCheckboxChange2(event) {
        isNormal = event.target.checked;
        
    }
    // @ts-ignore
    function handleCheckboxChange3(event) {
        isMax = event.target.checked;
        
    }
    

    let years = [];
    for (let year = 1970; year <= 2024; year++) {
        years.push(year);
    }
    let months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    
    let startYear = '';
    let endYear = '';
    let startMonth = '';
    
    let endMonth = '';
    /**
   * @type {any[]}
   */
    let items = [];
    // let inputValues = {};
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
        console.log("working");

        inputValues[index] = suggestion;
        suggestions[index] = [];
    }


    let desStats = [];
    let desStats_labels = ['Mean', 'Std', 'SR'];
    let corrStats = [];
    /**
   * @type {never[]}
   */
    let robust = [];
    function generateRange(start, end) {
        let range = [];
        for (let i = start; i <= end; i++) {
        range.push(i);
        }
        return range;
    }
    let range = generateRange(1, 100);


  // Function to handle form submission
  const handleSubmit = () => {
    // console.log(inputValues);
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
    for (let value of inputValues) {
      // @ts-ignore
      if (value.trim() !== "") {
        // @ts-ignore
        items = [...items, value.trim()];
      }
    }
    
    inputValues = Array(9).fill('');
  };

    async function processInput() {
        try {
            isLoading = true;
            await axios.post('http://127.0.0.1:5000/main', {
                ticker_list: items,
                Short: isShort,
                Max: isMax,
                Normal: isNormal,
                // @ts-ignore
                Start: Number(`${startYear}${startMonth}`),
                // @ts-ignore
                End: Number(`${endYear}${endMonth}`)
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
                // console.log(robust);
                let new_robust = {}

                for(const [key, value] of Object.entries(robust)){
                    // console.log(key, value);
                    if (key !== "Return" && key !== "SR" && key !== "Std"){
                        new_robust[key] = value;
                    }
                    
                }
                new_robust['Std'] = robust['Std']
                new_robust['SR'] = robust['SR']
                new_robust['Return'] = robust['Return']
                console.log(new_robust);
                robust = new_robust;
                // console.log(Object.keys(robust['Std']).length)
                updateChart(results.first_chart, results.second_chart, minX, maxX, minY, maxY, results.third_chart, results.third_chart_2);
            })
            
        } catch (error) {
            console.error('Error:', error);
        }
        items = []
    }

    // @ts-ignore
    function updateChart(dough, fill, minX, maxX, minY, maxY, combo, scatter) {
        const labels = items;
        const dataPoints = dough;
        const comboPoints = combo;
        const colors = labels.map(() => `#${Math.floor(Math.random()*16777215).toString(16)}`); // Generates random colors
 

        const fillPoints = fill.map((dataset, i) => {
            const color = colors[i];
            const rgbaColor = `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 0.5)`; 
            return {
                ...dataset,
                backgroundColor: rgbaColor,
                borderColor: color, 
                fill: true
            };
        });

        const scatterPoints = scatter.map((dataset, i) => {
            const color = colors[i];
            if(i == scatter.length - 1){
                return{
                    ...dataset,
                    backgroundColor: 'red',
                    borderColor: 'red', 
                }
            }
            // const rgbaColor = `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 0.5)`; 
            return {
                ...dataset,
                backgroundColor: color,
                borderColor: color, 
               
            };
        });

        

        // @ts-ignore
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
                // pointRadius: 10,
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
                // @ts-ignore
                borderWidth: 5,
                borderRadius: 2,
                hoverBorderWidth: 0,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                        boxWidth: 10,
                        padding: 3
                    }
                }
            }
        }});
    }


    onMount(() => {
        // Initialize chart with empty data
        // @ts-ignore
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

</script>

<body class="bg-black">

    <Navbar/>
    <div class="main-page text-[#C0C0C0]" style=" cursor: {isLoading ? 'wait' : 'auto'};">
        
        <div class="all-inputs">
            <div>
                <h2 class="mb-[3vh] text-xl">Advanced Options</h2>
                <div class="checks text-lg mb-[5vh]">
                    <div class="flex flex-row gap-[1vw] justify-center align-center">
                        <label><input class="w-[2.5vh] h-[2.5vh] rounded bg-[#2c2e2f]" type="checkbox" name="btn" on:change={handleCheckboxChange3} checked={isMax}></label>
                        <h2 class="">Maxuse</h2>
                        <div class="hover-container">
                            <i class="fa-solid fa-circle-question items-middle" style="color: #5ce07f;"></i>
                            <div class="hover-textbox">
                                Lorem ipsum odor amet, consectetuer adipiscing elit. Non quam inceptos natoque sem phasellus, ex euismod consequat luctus.
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-row gap-[1vw] justify-center align-center">
                        <label><input class="w-[2.5vh] h-[2.5vh]  rounded bg-[#2c2e2f]" type="checkbox" name="btn" on:change={handleCheckboxChange2} checked={isNormal}></label>
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
                <div class="grid grid-cols-4 w-[75%] gap-[2vw]">
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={startYear}>
                        {#each years as year}
                        <option class="text-sm rounded" value={year}>{year}</option>
                        {/each}
                    </select>
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={startMonth}>
                        {#each Object.entries(months) as [month, value]}
                        <option class="text-sm rounded" value={month}>{month}</option>
                        {/each}
                    </select>
                    
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={endYear}>
                        {#each years as year}
                        <option class="text-sm rounded" value={year}>{year}</option>
                        {/each}
                    </select>
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] bg-[#2c2e2f] text-base pl-[5%]" id="year-picker" bind:value={endMonth}>
                        {#each Object.entries(months) as [month, value]}
                        <option class="text-sm rounded" value={month}>{month}</option>
                        {/each}
                    </select>
                </div>
            </div>
            <div class="tickers mb-[5vh]">
                <h2 class="text-xl mb-[3vh]">Ticker Symbols</h2>
                <div class="grid grid-rows-3 grid-cols-3 gap-[2vh] w-[75%]">
            
                    {#each inputValues as inputValue, index}
                        <div class="relative">
                        <input
                            class="w-full bg-[#2c2e2f] h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md outline-none"
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
                                <option class="p-2 hover:bg-[#131217] cursor-pointer"  on:click={() => selectSuggestion(index, suggestion)}>
                                {suggestion}
                                </option>
                            {/each}
                            </ul>
                        {/if}
                        </div>
                    {/each}

                </div>
            </div>
            <button class="py-[10px] px-[30px] text-xl rounded-md hover:bg-[#2b2c30] ease-in-out duration-150 border-2 border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>
            
        </div>
        <div class="flex flex-col h-full items-center justify-center">
            <h1 class="text-4xl mb-[5vh]">Stock Doughnut Chart</h1>
            <div class="programming-stats">
                {#if nothing}
                    <p>Enter your desired portfolio</p>
                {/if}
                {#if !nothing}
                <canvas class="w-[50vh] my-chart"></canvas>
                {/if}
            </div>
            
        </div>
    </div>
    {#if !nothing}
    <div class="lgraph w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-4xl mb-[5vh] text-center text-[#C0C0C0]">Stock Line Fill Graph</h1>
        <div class="programming-stats max-h-[70vh] w-[70vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[55vw] min-w-[400px] line-chart"></canvas>
        </div>
    </div>
    <div class="bg-black w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-4xl mb-[5vh] text-center text-[#C0C0C0]">Scatter Line Graph</h1>
        <div class="programming-stats max-h-[70vh] w-[70vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[55vw] min-w-[400px] combo-chart"></canvas>
        </div>
    </div>
    <div class="rounded-t-[150px] bg-[#111111] w-[100vw] text-[#C0C0C0] mb-[15vh] pt-[15vh]">
        <div class="grid grid-cols-2 gap-[5vw] justify-self-center justify-center align-center">
        
            <div>
                <h1 class="text-center text-2xl mb-[5vh]">Asset Descriptive Statistics</h1>
                <ul class="grid grid-cols-3 gap-[1.4vw]">
                    {#each desStats as item}
                    <li class="programming-stats w-[20vh] h-[20vh] p-[2vh] bg-[#2c2e2f] rounded-lg border border-black/66">
                        {#each Object.entries(item) as [key, values]}
                        <div class="flex flex-col justify-center align-center h-full w-full">
                            <h2 class="text-base text-center font-bold">{key}</h2>
                            {#each values as value, index}
                              <p class="text-center">{desStats_labels[index]} - {value}</p>
                            {/each}
                          </div>
                        {/each}
                    </li>
                    {/each}
                </ul>
            </div>
            <div>
                <h1 class="text-center text-2xl mb-[5vh]">Asset Correlation Matrix</h1>
                
                <table class="w-[100%] border-collapse border border-gray-300">
                    <thead>
                      <tr class="bg-[#2c2e2f]">
                        <th class="border border-gray-300 p-3 text-center font-bold"> </th>
                        {#each Object.keys(corrStats) as key}
                          <th class="border border-gray-300 p-3 text-center font-bold">{key}</th>
                        {/each}
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.keys(corrStats) as rowKey}
                        <tr>
                          <th class="border bg-[#2c2e2f] border-gray-300 p-3 text-center font-medium">{rowKey}</th>
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
            <h1 class="text-center text-2xl mt-[5vh] mb-[5vh]">Robust Efficient Frontier Portfolios</h1>
            <div class="w-[80vw]">
                <Table shadow>
                    <TableHead>
                        <TableHeadCell>Index</TableHeadCell>
                        {#each Object.keys(robust) as key}
                            <TableHeadCell>{key}</TableHeadCell>
                        {/each}
                    </TableHead>
                    <TableBody tableBodyClass="divide-y  max-h-[40vh]">
                        {#each range as num}
                        <TableBodyRow>
                            <TableBodyCell>{num}</TableBodyCell>
                            {#each Object.keys(robust) as key}
                                <TableBodyCell>{robust[key][num]}</TableBodyCell>
                            {/each}
                        </TableBodyRow>
                        {/each}
                        
                    </TableBody>
                </Table>
            </div>
            
        </div>
    </div>
    
    
    {/if}
</body>


<style lang="css">
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap');
    @import '../app.css';


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
        /* background: linear-gradient(
        to right,
        #131217,
        #1a191d 25%,
        #0f0e10 50%,
        #1a191d 75%, 
        #0d0c0e 100% 
        ); */
        background: #0e0f13;

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
        /* align-items: center; */
        gap: 24px;
        margin: 0 auto;
        /* width: fit-content; */
        box-shadow: 0 4px 12px -2px rgba(255, 255, 255, .3);
        border-radius: 20px;
        padding: 8px 32px;
        color: white;
        transition: all 400ms ease;
        background-color: #2e3233;
    }
    .programming-stats:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 16px -7px rgba(255, 255, 255, .6);
    }
    .programming-stats .details ul {
        list-style: none;
        padding: 0;
    }

    .lgraph{
        background: linear-gradient(
  to bottom,
  #0e0f13,
  #0c0d10 40%, 
  black 100% 
);
    }
    
    
</style>