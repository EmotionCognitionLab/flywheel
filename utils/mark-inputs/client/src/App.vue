<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'app'
}
</script>

<style>
  body {
    font: 16px "Helvetica Neue", Helvetica, arial, sans-serif;
    font-weight: 400;
  }

  .clickable-row:hover {
    background-color: #f8f9fb;
  }
</style>