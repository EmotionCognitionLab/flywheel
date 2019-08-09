<template>
    <div v-if="files.length" id="selectedFilesList" class="compact-tag">
        <div v-if="taggingStatus == 'untagged' || taggingStatus == 'editing' || taggingStatus == 'might-edit'">
            <input 
                v-model="tag"
                @keyup.enter="saveTag"
                @keydown.tab="saveTag"
                @click="setEditStatus('editing')"
                @mouseleave="hideTextInput"
                placeholder="Enter a tag for these files"
                id="tag-field">
                <button @click="saveTag">Save</button>
        </div>
        <span v-else @mouseenter="setEditStatus('might-edit')" class="tag-name">{{ tag }}</span>
        <br/>
        <ul>
            <li v-for="(file, index) in files" 
            :key="index"
            class="mini-file">
            {{ file.name }}
            </li>
        </ul>
    </div>
</template>

<script>
import TagManager from '../../services/TagManager'

export default {
    computed: {
        allTags: function() {
            return TagManager.getAllTags()
        }
    },
    data() {
        return {
            tag: this.initialTag,
            taggingStatus: !this.tag && !this.initialTag ? 'untagged' : 'tagged',
            timer: null
        }
    },
    methods: {
        hideTextInput: function() {
            if (this.timer != null) {
                clearInterval(this.timer);
                this.timer = null;
            }
            if (this.taggingStatus == 'might-edit') {
                this.timer = setInterval(function() { // TODO handle multiple timers?
                    this.taggingStatus = 'tagged'
                }.bind(this), 200);
            }
        },
        saveTag: function() {
            if (this.storeTaggedFiles()) {
                this.taggingStatus = 'tagged'
                this.$emit('tag-list-changed')
            }
        },
        setEditStatus: function(status) {
            if (this.timer != null) {
                clearInterval(this.timer);
                this.timer = null;
            }
            this.taggingStatus = status;
        },
        storeTaggedFiles: function() {
            if (this.tag != '') {
                return TagManager.save({tag: this.tag, files: this.files})
            } else {
                alert('You must enter a tag before continuing.')
                return false;
            }
        }
    },
    props: {
        files: {
            type: Array,
            required: true
        },
        initialTag: {
            type: String,
            required: true
        }
    }
}
</script>

<style>
    .compact-tag {
        background: rgb(240, 240, 240);
        border: 2px solid grey;
        border-radius: 15px;
        max-width: 40%;
        padding: 10px;
        margin-bottom: 20px;
    }
    .mini-file {
        font-size: 0.75em;
        border: none;
        list-style-type: disc;
        padding: 0;
    }
    #tag-field {
        margin: 0 5px 10px 0;
        border-radius: 10px;
    }
    .tag-name {
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
