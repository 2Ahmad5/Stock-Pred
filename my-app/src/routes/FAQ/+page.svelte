<script>
let corrStats = {
    "AAPL": {"AAPL": 1.00, "AMZN": 0.38, "NVDA": 0.45},
    "AMZN": {"AAPL": 0.38, "AMZN": 1.00, "NVDA": 0.33},
    "NVDA": {"AAPL": 0.45, "AMZN": 0.33, "NVDA": 1.00},
    
}
</script>
<body>
    <div class="p-[3vh] bg-[#27292b] mb-[2vh] shadow-xl rounded-lg">
      <table class="border-collapse border border-gray-300">
        <thead>
          <tr class="bg-gray-100">
            <th class="border border-gray-300 p-3 text-center font-bold"> </th>
            {#each Object.keys(corrStats) as key}
              <th class="border border-gray-300 p-3 text-center font-bold">{key}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each Object.keys(corrStats) as rowKey}
            <tr>
              <th class="border border-gray-300 bg-gray-100 p-3 text-center font-bold ont-medium">{rowKey}</th>
              {#each Object.keys(corrStats[rowKey]) as colKey}
                <td class="border border-gray-300 text-center p-3 hover:bg-gray-100 transition-all ease-in-out duration-200">
                  <p class="text-base font-mono">{corrStats[rowKey][colKey].toFixed(2)}</p>
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    
</body>