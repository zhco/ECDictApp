package com.example.ecdictapp

import kotlinx.coroutines.flow.Flow

interface DictDao {
    suspend fun lookup(word: String): DictEntry?
    fun lookupFlow(word: String): Flow<DictEntry?>
    suspend fun searchPrefix(prefix: String, limit: Int = 20): List<SearchResult>
    fun searchPrefixFlow(prefix: String, limit: Int = 20): Flow<List<SearchResult>>
    suspend fun count(): Int
}
