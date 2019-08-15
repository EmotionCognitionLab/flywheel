<template>
    <div>
        <div v-if="status.message" >
            <div id="status" :class="status.type" class="status">
                <p>{{ status.message }}</p>
            </div>
            <div v-if="status.type == 'info'">
                <a href="/projects">Start over</a>
            </div>
            <div v-else>
                <a href="#" @click.stop="status.message = ''">Try again</a>
            </div>
        </div>
        <div v-else>
            <div id="input-container">
                <p>All of the tags below will be uploaded to a file
                    attached to the project {{projectLabel}}.</p>
                
                <label for="filename">Enter a name for the tag file: </label>
                <input
                v-model="filename"
                @keyup.enter="upload"
                placeholder="my-files-to-analyze.json"
                id="filename">
                <button id="upload" ref="uploadBtn" @click="upload">Upload</button>
            </div>
            <TaggedFiles v-for="(taggedFiles, index) in allTags"
            :key="index"
            :files=taggedFiles.files
            :initialTag=taggedFiles.tag
            @tag-list-changed="onTagListChanged"
            >
            </TaggedFiles>
        </div>
    </div>
</template>
<script>
import { Flywheel } from '../../services/Flywheel'
import TagManager from '../../services/TagManager'
import TaggedFiles from './TaggedFiles'

let fw
export default {
    components: { TaggedFiles },
    created() {
        this.allTags = TagManager.getAllTags()
    },
    data() {
        return {
            allTags: {},
            filename: '',
            status: { type: 'info', message: '' }
        }
    },
    methods: {
        onTagListChanged: function() {
            this.allTags = TagManager.getAllTags()
        },
        upload: function() {
            this.$refs.uploadBtn.innerText = "Uploading..."
            this.$refs.uploadBtn.disabled = true
            if (!fw) fw = new Flywheel(sessionStorage.fwApiKey, process.env.VUE_APP_FW_URL)
            fw.uploadFileToProject(this.projectId, this.filename, this.allTags, 'application/json')
            .then(() => {
                this.status.message = "File uploaded successfully"
                this.status.type = "info"
                TagManager.deleteAllTags()
            })
            .catch(err => {
                this.status.message = "Error uploading file"
                this.status.type = "error"
                console.log(err)
            })
        }
    },
    props: {
        projectId: {
            type: String,
            required: true
        },
        projectLabel: {
            type: String,
            required: true
        }
    }
}
</script>
<style>
    .error {
        background-color: indianred;
    }
    #filename {
        margin-right: 10px;
    }
    .info {
        background-color: lightgreen;
    }
    #input-container {
        margin-bottom: 30px;
    }
    #input-container button {
        font-size: 16px;
        padding: 6px;
    }
    .status {
        border-radius: 20px;
        font-weight: 400;
        padding: 8px;
        margin-left: 20%;
        max-width: 40%;
        text-align: center;
    }
    #upload {
        cursor: pointer;
    }
</style>
