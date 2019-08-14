<template>
    <div 
    class="acquisition "
    :data-sessid="acquisition.parent"
    >
        <div class="header">{{ acquisition.label }}</div>
        <div v-if="acquisition['files'].length" class="file-list" >
            <div
            v-for="output in acquisition['files']"
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
            <h4>No acquisitions</h4>
        </div>
    </div>
</template>

<script>
export default {
    methods: {
        fileClick: function(event) {
            const acquisitionNode = event.target.closest('.acquisition')
            const acquisitionId = acquisitionNode.dataset.sessid
            this.$emit('file-clicked', 
            {
                selected: event.target.checked,
                file: { 
                    id: acquisitionId,
                    name: event.target.dataset.name,
                    parentType: 'acquisition' 
                } 
            })
        }
    },
    props: {
        acquisition: {
            type: Object,
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
