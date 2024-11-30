
<script>
    let y;
</script>

<body>
    <div class="navbar {y < 50 ? 'h-[10vh]' : 'h-[7vh]'}">

        <div>
            Logo/Name goes here
        </div>
        <div class="flex gap-[2vh] w-[90%] items-center justify-between text-[#D3D3D3] text-lg">
            <a class="hover:text-white ease-in-out duration-200">Home</a>
            <a class="hover:text-white">Mean-variance</a>
            <a href="/Regression" class="hover:text-white">Regression</a>
            <a href="/Backtesting" class="hover:text-white">Backtesting</a>
            <a href="/FAQ" class="hover:text-white">FAQ</a>
        </div>
    </div>
</body>

<svelte:window bind:scrollY={y}/>


<style lang="css">
    @import '../app.css';

    .navbar a{
        position: relative;
        cursor: pointer;
    }


    .navbar a::after{
        content: '';
        position: absolute;
        height: 2px;
        border-radius: 10px;
        left: 0;
        bottom: 0;
        width: 0;
        background: white;
        transition: width .2s;
    }

    .navbar a:hover::after{
        width: 100%;
    }

    .navbar{
        z-index: 40;
        position: fixed;
        width: 100vw;
        /* height: 10vh; */
        transition: height .6s;
        display: grid;
        grid-template-columns: 55vw 45vw;
        background: black;
    }
</style>
