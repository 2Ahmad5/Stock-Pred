<script>
    //@ts-ignore
    import { onMount } from 'svelte';
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
        Filler
    } from 'chart.js';

    
    Chart.register(DoughnutController, ArcElement, Tooltip, Legend, CategoryScale, LineController, LineElement, PointElement, LinearScale, Title, Filler);

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
    let inputValues = {};

  // Function to handle form submission
  const handleSubmit = () => {
    nothing = false;
    for (let key in inputValues) {
      // @ts-ignore
      if (inputValues[key].trim() !== "") {
        // @ts-ignore
        items = [...items, inputValues[key].trim()];
      }
    }
    
    inputValues = {};
  };

    async function processInput() {
        console.log(items);
        try {
            const response = await axios.post('http://127.0.0.1:5000/process', {
                ticker_list: items,
                Short: isShort,
                Max: isMax,
                Normal: isNormal,
                // @ts-ignore
                Start: Number(`${startYear}${months[startMonth]}`),
                // @ts-ignore
                End: Number(`${endYear}${months[endMonth]}`)
            });
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

            
            console.log(results, minX, maxX, minY, maxY);
            updateChart(results.first_chart, results.second_chart, minX, maxX, minY, maxY);
        } catch (error) {
            console.error('Error:', error);
        }
        items = []
    }

    // @ts-ignore
    function updateChart(dough, fill, minX, maxX, minY, maxY) {
        const labels = items;
        const dataPoints = dough;

        const colors = labels.map(() => `#${Math.floor(Math.random()*16777215).toString(16)}`); // Generates random colors
 

        const fillPoints = fill.map((dataset, i) => {
            const color = colors[i];
            const rgbaColor = `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 0.5)`; // Convert hex to rgba with 50% transparency
            return {
                ...dataset,
                backgroundColor: rgbaColor,
                borderColor: color, 
                fill: true
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
    <!-- <h1>Input Values</h1>
    <input type="text" bind:value={userInput} placeholder="Enter values separated by commas" />
    <button on:click={processInput}>Submit</button>

    <h2>Results</h2>
    <pre>{JSON.stringify(results, null, 2)}</pre>

    <h2 class="chart-heading">Stock Percents</h2>
    <div class="programming-stats">
        <div class="chart-container">
            <canvas class="my-chart"></canvas>
        </div>

        <div class="details">
            <ul></ul>
        </div>
    </div> -->
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
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[0]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[1]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[2]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[3]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[4]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[5]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[6]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[7]}>
                    <input class="w-full h-[5vh] p-[10px] border-2 border-[#696a6b] rounded-md" type="text" placeholder="Place ticker here..." bind:value={inputValues[8]}>

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
        width: fit-content;
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
