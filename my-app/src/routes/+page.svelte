<script>
    //@ts-ignore
    import { onMount } from 'svelte';
    import { openDB } from 'idb';
    import axios from 'axios';
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

    
    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler, ScatterController);

    // @ts-ignore
    let userInput = '';
    let results = {};
    // @ts-ignore
    let doughnut_chart;
    let line_chart;
    let combo_chart;

    let isShort = true;
    let isMax = true;
    let isNormal = true;
    let nothing = true;
    let csvData = []
    let etflist = []

    onMount(async () => {
        const db = await openDB('csvStore', 1, {
        upgrade(db) {
            db.createObjectStore('keyval');
        },
        });

        const storedCsvData = await db.get('keyval', 'csvData');
        const storedEtfList = await db.get('keyval', 'etfList');

        if (storedCsvData && storedEtfList) {
            csvData = storedCsvData;
            etflist = storedEtfList;
        }else{
            const response = await fetchCsv('/ETF_returns_v2.csv');
            if (response.ok) {
                const csvText = await response.text();
                csvData = JSON.parse(csvJSON(csvText));
                etflist = extractColumnValues(csvData, 'ticker_new');
                console.log(etflist)

                await db.put('keyval', csvData, 'csvData');
                await db.put('keyval', etflist, 'etfList');
            }
        }
    
    });

    function extractColumnValues(data, column) {
        const values = new Set();
        data.forEach(row => {
        if (row[column] !== undefined) {
            values.add(row[column]);
        }
        });
        return Array.from(values);
    }

    function csvJSON(csv) {
    var lines = csv.split("\n");
    var result = [];
    var headers = lines[0].split(",");

    for (var i = 1; i < lines.length; i++) {
      var obj = {};
      var currentline = lines[i].split(",");

      for (let j = 0; j < headers.length; j++) {
        const header = headers[j] ? headers[j].trim() : '';
        const value = currentline[j] ? currentline[j].trim() : '';
        obj[header] = value;
      }

      if (Object.keys(obj).some(key => obj[key] !== '')) {
        result.push(obj);
      }
    }
    return JSON.stringify(result);
  }

    async function fetchCsv(filePath){
        try{
            const response = await fetch(filePath);
            return response; 
        } catch(error) {
            console.error('Error fetching or parsing CSV file:', error);
        }
    }

    

    // @ts-ignore
    function handleCheckboxChange1(event) {
        isShort = !event.target.checked;
        
    }
    // @ts-ignore
    function handleCheckboxChange2(event) {
        isNormal = !event.target.checked;
        
    }
    // @ts-ignore
    function handleCheckboxChange3(event) {
        isMax = !event.target.checked;
        
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

    function selectSuggestion(index, suggestion) {
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
        // console.log(items);
        try {
            // const response = await axios.post('http://127.0.0.1:5000/process', {
            await axios.post('http://127.0.0.1:5000/process', {
                ticker_list: items,
                Short: isShort,
                Max: isMax,
                Normal: isNormal,
                // @ts-ignore
                Start: Number(`${startYear}${startMonth}`),
                // @ts-ignore
                End: Number(`${endYear}${endMonth}`)
            }).then((response ) => {
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
                console.log(robust);
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
                            text: 'Allocation'
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
            }
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
                    data: dataPoints,
                    backgroundColor: colors
                }]
            },
            options: {
                // @ts-ignore
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

<body>
    <div class="main-page">
        <div class="all-inputs">
            <div>
                <h2 class="mb-[3vh] text-2xl">Advanced Options</h2>
                <div class="checks text-xl mb-[5vh]">
                    <div>
                        <h2>Shorts</h2>
                        <label><input type="checkbox" name="btn" on:change={handleCheckboxChange1} checked={!isShort}></label>
                    </div>
                    <div>
                        <h2>Maxuse</h2>
                        <label><input type="checkbox" name="btn" on:change={handleCheckboxChange3} checked={!isMax}></label>
                        
                    </div>
                    <div>
                        <h2>Normal</h2>
                        <label><input type="checkbox" name="btn" on:change={handleCheckboxChange2} checked={!isNormal}></label>
                    </div>
                </div>
                
            </div>
            <div class="dates mb-[5vh]">
                <h2 class="text-2xl mb-[3vh]">Picking Dates (Start Yr/Month. End Yr/Month)</h2>
                <div class="grid grid-cols-4 w-[90%] gap-[2vw]">
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl" id="year-picker" bind:value={startYear}>
                        {#each years as year}
                        <option class="text-sm rounded" value={year}>{year}</option>
                        {/each}
                    </select>
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl" id="year-picker" bind:value={startMonth}>
                        {#each Object.entries(months) as [month, value]}
                        <option class="text-sm rounded" value={month}>{month}</option>
                        {/each}
                    </select>
                    
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl" id="year-picker" bind:value={endYear}>
                        {#each years as year}
                        <option class="text-sm rounded" value={year}>{year}</option>
                        {/each}
                    </select>
                    <select class="border-2 flex justify-center items-center rounded h-[4vh] border-[#696a6b] text-xl" id="year-picker" bind:value={endMonth}>
                        {#each Object.entries(months) as [month, value]}
                        <option class="text-sm rounded" value={month}>{month}</option>
                        {/each}
                    </select>
                </div>
            </div>
            <div class="tickers mb-[5vh]">
                <h2 class="text-2xl mb-[3vh]">Ticker Symbols</h2>
                <div class="grid grid-rows-3 grid-cols-3 gap-[2vh] w-[95%]">
            
                    {#each inputValues as inputValue, index}
                        <div class="relative">
                        <input
                            class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md"
                            type="text"
                            placeholder="Place ticker here..."
                            bind:value={inputValues[index]}
                            on:input={(e) => updateSuggestions(index, e.target.value)}
                        >
                        {#if suggestions[index].length > 0}
                            <ul class="absolute bg-white border border-gray-300 w-full mt-1 rounded-md z-10">
                            {#each suggestions[index] as suggestion}
                                <li class="p-2 hover:bg-gray-200 cursor-pointer"  on:click={() => selectSuggestion(index, suggestion)}>
                                {suggestion}
                                </li>
                            {/each}
                            </ul>
                        {/if}
                        </div>
                    {/each}

                </div>
            </div>
            <button class="py-[10px] px-[30px] text-xl rounded-md hover:bg-[#5ce07f] ease-in-out duration-150 border-2 border-[#696a6b]" on:click={handleSubmit} on:click={processInput}>Submit</button>
            
        </div>
        <div class="flex flex-col rounded-bl-[15vh] bg-[#5ce07f] h-full items-center justify-center">
            <h1 class="text-4xl mb-[5vh]">Stock Doughnut Chart</h1>
            <div class="programming-stats bg-white">
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
    <div class="w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-4xl mb-[5vh] text-center">Stock Line Fill Graph</h1>
        <div class="programming-stats max-h-[80vh] w-[80vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[75vw] min-w-[400px] line-chart"></canvas>
        </div>
    </div>
    <div class="w-full h-[100vh] flex flex-col justify-center align-center">
        <h1 class="text-4xl mb-[5vh] text-center">Scatter Line Graph</h1>
        <div class="programming-stats max-h-[80vh] w-[80vw] min-w-[400px] p-[5vh]">
            <canvas class="w-[75vw] min-w-[400px] combo-chart"></canvas>
        </div>
    </div>

    <div class="max-w-[90vw] ml-[5vw] mb-[15vh] mt-[15vh] grid grid-cols-2 justify-self-center justify-center align-center">
        
        <div>
            <h1 class="text-center text-4xl mb-[5vh]">Asset Descriptive Statistics</h1>
            <ul class="grid grid-cols-3 gap-[1.4vw]">
                {#each desStats as item}
                <li class="programming-stats w-[90%] h-[30vh] py-[6vh] px-[3vw]">
                    {#each Object.entries(item) as [key, values]}
                    <div class="flex flex-col justify-center align-center h-full w-full">
                        <h2 class="text-xl text-center font-bold">{key}</h2>
                        {#each values as value, index}
                          <p class="text-center ">{desStats_labels[index]} - {value}</p>
                        {/each}
                      </div>
                    {/each}
                </li>
                {/each}
            </ul>
        </div>
        <div>
            <h1 class="text-center text-4xl mb-[5vh]">Asset Correlation Matrix</h1>
            <table class="w-[90%]">
                <thead>
                  <tr class="flex w-full">
                    <th class="w-full"></th>
                    {#each Object.keys(corrStats) as key}
                      <th class="w-full"><p class="text-center mb-[3vh]">{key}</p></th>
                    {/each}
                  </tr>
                </thead>
                <tbody class="grid gap-[15px]">
                  {#each Object.keys(corrStats) as rowKey}
                    <tr class="flex w-full gap-[15px]">
                      <th class="w-full grid items-center justify-center"><p>{rowKey}</p></th>
                      {#each Object.keys(corrStats[rowKey]) as colKey}
                        <td class="w-[85%] programming-stats h-[10vh] text-center shadow-xl rounded-lg grid items-center justify-center"><p class="text-lg">{corrStats[rowKey][colKey].toFixed(2)}</p></td>
                      {/each}
                    </tr>
                  {/each}
                </tbody>
            </table>
        </div>
    </div>
    <div class="w-full flex flex-col justify-center items-center">
        <h1 class="text-center text-4xl mb-[5vh]">Robust Efficient Frontier Portfolios</h1>
        <div class="w-[80vw] mb-[15vh]">
            <Table shadow>
                <TableHead>
                    {#each Object.keys(robust) as key}
                        <TableHeadCell>{key}</TableHeadCell>
                    {/each}
                </TableHead>
                <TableBody tableBodyClass="divide-y">
                    {#each range as num}
                    <TableBodyRow>
                        {#each Object.keys(robust) as key}
                            <TableBodyCell>{robust[key][num]}</TableBodyCell>
                        {/each}
                    </TableBodyRow>
                    {/each}
                    
                </TableBody>
            </Table>
        </div>
        
    </div>
    {/if}
</body>

<style lang="css">
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap');
    @import '../app.css';

    select:focus{
        outline: none;
    }
    input:focus{
        outline: none;
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
        margin-left: 10vw;
    }

    .checks{
        display: flex;
        flex-direction: row;
        gap: 5vw;
    }

    .checks h2{
        text-align: center;
    }

    input[type="checkbox"]{
        position: relative;
        width: 100px;
        height: 30px;
        margin: 10px;
        outline: none;
        background: #5ce07f;
        -webkit-appearance: none;
        cursor: pointer;
        border-radius: 20px;
        box-shadow: -5px -5px 20px rgba(255, 255, 255, .1),
        5px 5px 10px rgba(0,0,0,1), inset -2px -2px 5px rgba(255, 255, 255, .1), inset 2px 2px 5px rgba(0,0,0,.5), 0 0 0 2px #1f1f1f;
        transition: .5s;
    }

    input[type="checkbox"]:checked{
        background: #111;
    }

    input[type="checkbox"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 40px;
    width: 60px;
    height: 30px;
    background: linear-gradient(to top, #000, #555);
    border-radius: 20px;
    box-shadow: 0 0 0 1px #232323;
    transform: scale(0.98, 0.96);
    transition: 0.5s;
}

input[type="checkbox"]:checked::before {
    left: 0;
}

input[type="checkbox"]::after {
    content: '';
    position: absolute;
    top: -webkit-calc(50% - 2px);
    top: calc(50% - 2px);
    width: 4px;
    height: 4px;
    border-radius: 50%;
    left: -webkit-calc(45px + 40px);
    left: calc(45px + 40px);
    background-color: #5ce07f;
    box-shadow: 0 0 5px #5ce07f, 0 0 15px #5ce07f, 0 0 30px #5ce07f;
    transition: 0.5s;
}

input[type="checkbox"]:checked::after {
    left: 45px;
    box-shadow: 0 0 0 1px #232323;
    background: #555;
}

    .chart-heading {
        font-family: 'Rubik', sans-serif;
        color: #023047;
        text-transform: uppercase;
        font-size: 24px;
        text-align: center;
    }

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
