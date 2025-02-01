<script>
    import { createEventDispatcher } from 'svelte';

    export let selectedMonthYear = '';

    const dispatch = createEventDispatcher();

    function handleDateSelect(event) {
        selectedMonthYear = event.target.value;
        dispatch('monthSelected', { monthYear: selectedMonthYear });
    }
</script>

<div class="month-picker">
    <input type="month" bind:value={selectedMonthYear} on:change={handleDateSelect} />

</div>

<style lang='css'>
        .month-picker {
        display: inline-block;
        position: relative;
    }

    .month-picker input {
        padding: 10px 15px;
        font-size: 16px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
        color: #333333;
        cursor: pointer;
        transition: all 0.3s ease;
        outline: none;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .month-picker input:hover {
        border-color: #bdbdbd;
    }

    .month-picker input:focus {
        border-color: #2196f3;
        box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
    }

    /* Styling the calendar icon */
    .month-picker input::-webkit-calendar-picker-indicator {
        color: #757575;
        font-size: 18px;
        cursor: pointer;
        transition: color 0.3s ease;
    }

    .month-picker input::-webkit-calendar-picker-indicator:hover {
        color: #2196f3;
    }
</style>
