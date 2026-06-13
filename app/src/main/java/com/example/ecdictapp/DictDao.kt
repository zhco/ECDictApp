package com.example.ecdictapp

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface DictDao {

    @Query("SELECT * FROM dictionary WHERE word = :word LIMIT 1")
    suspend fun lookup(word: String): DictEntry?

    @Query("SELECT * FROM dictionary WHERE word = :word LIMIT 1")
    fun lookupFlow(word: String): Flow<DictEntry?>

    @Query("SELECT word, translation FROM dictionary WHERE word LIKE :prefix || '%' ORDER BY word LIMIT :limit")
    suspend fun searchPrefix(prefix: String, limit: Int = 20): List<SearchResult>

    @Query("SELECT word, translation FROM dictionary WHERE word LIKE :prefix || '%' ORDER BY word LIMIT :limit")
    fun searchPrefixFlow(prefix: String, limit: Int = 20): Flow<List<SearchResult>>

    @RawQuery
    suspend fun rawQuery(query: SupportSQLiteQuery): List<DictEntry>

    @Query("SELECT COUNT(*) FROM dictionary")
    suspend fun count(): Int
}
