<template>
    <div>
        <div v-if="!hasSeenTaggerIntro" id="intro">
            Welcome to Tagger! Tagger is a tool to help you specify inputs for Flywheel analyses.
            It allows you to select one or more files (either from outputs of existing analyses,
            or from acquisitions) and associate them with a tag. You can create as many
            tag/file groups as you want. Once you're done, Tagger will upload them all to a file in Flywheel.
            You can then use that file as an input to a Flywheel analysis.
            <br/>
            <div id="intro-controls">
                <span>
                    <input type="checkbox" id="do-not-show" v-model="doNotShowIntroAgain">
                    <label for="do-not-show">Do not show this again</label>
                </span>
                <span id="button-holder"><button @click="setIntroSeen">Got it!</button></span>
            </div>
        </div>
        <div v-else id="api-key">
            Enter your <a href="https://uscdni.flywheel.io/#/profile" target="_blank">Flywheel API key</a>: <input v-model="fwApiKey">
            <button 
                @click="setApiKey"
                class="navBtn">
                Next >>
            </button>
        </div>
    </div>
</template>

<script>

export default {
    name: 'ApiKey',
    data() {
        return {
            doNotShowIntroAgain: true,
            hasSeenTaggerIntro: false,
            fwApiKey: ''
        }
    },
    methods: {
        setApiKey() {
            sessionStorage.fwApiKey = this.fwApiKey
            this.$router.push({ path: '/projects' })
        },
        setIntroSeen() {
            if (this.doNotShowIntroAgain) {
                localStorage.hasSeenTaggerIntro = true
            }
            this.hasSeenTaggerIntro = true
        }
    },
    mounted() {
        if (sessionStorage.fwApiKey) {
            this.fwApiKey = sessionStorage.fwApiKey
        }
        this.hasSeenTaggerIntro = localStorage.hasSeenTaggerIntro
    }
}
</script>

<style>
    #api-key {
        margin: 150px;
        font-size: 20px;
    }
    #button-holder {
        float: right;
    }
    #do-not-show {
        width: 12px;
    }
    #intro-controls {
        padding: 12px;
    }
    #intro-controls span label {
        font-size: 0.8em;
        color: rgb(107, 100, 100);
    }
    input {
        padding: 7px;
        width: 175px;
    }
    #intro {
        width: 700px;
        height: 120px;
        background-color: aliceblue;
        margin: 50px 50px 50px 50px;
        padding: 20px;
    }
    .navBtn {
        margin-left: 10px;
        padding: 3px;
    }
</style>


