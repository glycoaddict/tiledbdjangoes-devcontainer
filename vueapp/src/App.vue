<template>
  <div>
    <button class="btn btn-primary rounded-pill px-3" type="button">Primary</button>
    <!-- <QueryInput @form-submitted="results => data = results" />
    <MyTable :table-data="results.answer" />
    <MyQuerySummary :table-data="data.query_summary" /> -->
    <!-- <QueryInput v-on:search="searchVCF" /> -->
    <!-- <MyTable v-if="result" :data="result.answer" />
    <MyQuerySummary v-if="result" :data="result.query_summary" /> -->
  </div>
</template>

<script>
import QueryInput from "./components/QueryInput.vue";
import MyTable from "./components/MyTable.vue";
import MyQuerySummary from "./components/MyQuerySummary.vue";
import axios from "axios";

export default {
  name: "App",
  components: {
    QueryInput,
    MyTable,
    MyQuerySummary,
  },
  data() {
    return {
      result: null,
    };
  },
  methods: {
    searchVCF(queryInput) {
      axios
        .post("http://localhost:8000/vcf-query", {
          regions: queryInput.regions,
          samples: queryInput.sample_name,
          attrs: "id,alleles,fmt_GT,contig,pos_start,pos_end,info_AF",
          clinvar: false,
          hidenonvariants: false,
          genelist: false,
        })
        .then((response) => {
          this.result = response.data;
          console.log("data received!");
        })
        .catch((error) => {
          console.log(error);
        });
    },
  },
};
</script>
