
<script>
    
    let y;
    let currentPath = "";

    $: {
        if (typeof window !== "undefined") {
            currentPath = window.location.pathname;
        }
    }

    function isActive(path) {
        return currentPath === path ? 'text-[#5ce07f]' : 'text-black';
    }
</script>

<body>
<div class="navbar h-[10vh]">

    <div class="options flex gap-[2vw] w-fit items-center justify-center text-black text-base px-[25px]">
        <a class="hover:text-[#5ce07f] ease-in-out duration-200 {isActive('/')}" href="/">Home</a>
        <a class="hover:text-[#5ce07f] {isActive('/Mean')}" href="/Mean">Mean-variance</a>
        <a class="hover:text-[#5ce07f] {isActive('/Regression')}" href="/Regression" >Regression</a>
        <a class="hover:text-[#5ce07f] {isActive('/Backtesting')}" href="/Backtesting">Backtesting</a>
        <a class="hover:text-[#5ce07f] {isActive('/FAQ')}" href="/FAQ">FAQ</a>
    </div>
</div>
</body>

<svelte:window bind:scrollY={y}/>


<style lang="css">
    @import '../../app.css';

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
        background: #5ce07f;
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
        align-items: center;
        justify-content: center;
        /* background: black; */
    }

    .options{
        height: 50%;
        border-radius: 25px;
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(6.9px);
        -webkit-backdrop-filter: blur(6.9px);

    }
</style>
