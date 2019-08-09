import isEqual from 'lodash.isequal'

export default {
    getAllTags: function() {
        var tagList = sessionStorage.tagList
            if (!tagList) {
                tagList = []
            } else {
                tagList = JSON.parse(tagList)
            }
            return tagList
    },

    // tagObj is { tag: 'some-tag', files: [{analysis_id:'', name:''}, ...] }
    save: function (tagObj) {
        // Note: it is not possible to save the exact same set of files
        // with two different tags
        if (tagObj.tag == undefined || !tagObj.files) return false

        const tagList = this.getAllTags()
        var isSaved = false
        for (var i=0; i<tagList.length; i++) {
            if (isEqual(tagObj.files, tagList[i].files)) {
                tagList[i].tag = tagObj.tag
                isSaved = true
            }
        }
        if (!isSaved) tagList.unshift(tagObj) // put it at the front of the list so that when we add an item that needs a tag it shows up first
        sessionStorage.tagList = JSON.stringify(tagList)
        return true;
    },

    deleteAllTags: function() {
        sessionStorage.removeItem('tagList')
    }
}