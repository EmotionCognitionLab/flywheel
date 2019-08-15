<template>
    <div 
    class="file-container"
    :data-sessid="fileContainer.parent"
    :data-id="fileContainer.id"
    >
        <div class="header">{{ fileContainer.label }}</div>
        <div v-if="fileContainer['files'].length" class="file-list" >
            <div
            v-for="file in fileContainer['files']"
            :key="file['id']">
                <input
                type="checkbox"
                :checked="file.isSelected"
                :id="file['id']"
                :data-name="file['name']"
                v-on:change="fileClick"
                class="list-checkbox" />
                <label :for="file['id']">{{ file['name'] }}</label>
            </div>
        </div>
        <div v-else class="file-list">
            <h4>{{ noFilesText }}</h4>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        noFilesText() {
            if (this.fileContainer.parentType == 'analysis') {
                return "No analysis outputs."
            } else {
                return "No files."
            }
        }
    },
    methods: {
        fileClick: function(event) {
            const fileContainerNode = event.target.closest('.file-container')
            const fileContainerId = fileContainerNode.dataset.id
            const sessId = fileContainerNode.dataset.sessid
            this.$emit('file-clicked', 
            {
                selected: event.target.checked,
                file: { 
                    parentId: fileContainerId,
                    sessId: sessId,
                    name: event.target.dataset.name,
                    parentType: this.fileContainer.parentType 
                } 
            })
        }
    },
    props: {
        fileContainer: {
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
