<template>
    <div 
    class="analysis "
    :class="{ hidden: hide }"
    :data-sessid="analysis.parent"
    >
        <div class="header">{{ analysis.label }}</div>
            <div v-if="analysis['files'].length" class="file-list" >
                <div
                v-for="output in analysis['files']"
                :key="output['id']">
                    <input
                    type="checkbox"
                    :id="output['id']"
                    :data-name="output['name']"
                    v-on:change="fileClick"
                    class="list-checkbox" />
                    <label :for="output['id']">{{ output['name'] }}</label>
                </div>
            </div>
            <div v-else class="file-list">
                <h4>No output files</h4>
            </div>
    </div>
</template>

<script>
export default {
    methods: {
        fileClick: function(event) {
            const analysisNode = event.target.closest('.analysis')
            const analysisId = analysisNode.dataset.sessid
            this.$emit('file-clicked', 
            { selected: event.target.checked, 
              file: { analysisId: analysisId, name: event.target.dataset.name } })
        }
    },
    props: {
        analysis: {
            type: Object,
            required: true
        },
        hide: {
            type: Boolean,
            required: true
        }
    }
}
</script>

<style>
    .file-list {
        margin-left: 15px;
    }
    .header {
        padding: 10px 0px 10px 10px;
        margin: 5px 0px 5px 0px;
        background-color: rgb(163, 155, 155);
    }
</style>
