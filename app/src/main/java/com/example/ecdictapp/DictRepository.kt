package com.example.ecdictapp

import kotlinx.coroutines.flow.Flow

class DictRepository(private val dao: DictDao) {

    suspend fun lookup(word: String): DictEntry? {
        return dao.lookup(word.trim().lowercase())
    }

    fun lookupFlow(word: String): Flow<DictEntry?> {
        return dao.lookupFlow(word.trim().lowercase())
    }

    suspend fun searchPrefix(prefix: String, limit: Int = 20): List<SearchResult> {
        if (prefix.isBlank()) return emptyList()
        return dao.searchPrefix(prefix.trim().lowercase(), limit)
    }

    fun searchPrefixFlow(prefix: String, limit: Int = 20): Flow<List<SearchResult>> {
        return dao.searchPrefixFlow(prefix.trim().lowercase(), limit)
    }

    suspend fun count(): Int {
        return dao.count()
    }
}
