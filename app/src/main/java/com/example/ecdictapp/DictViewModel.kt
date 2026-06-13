package com.example.ecdictapp

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

class DictViewModel(private val repository: DictRepository) : ViewModel() {

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    private val searchDebounce = MutableStateFlow("")

    init {
        viewModelScope.launch {
            _searchQuery
                .debounce(300)
                .distinctUntilChanged()
                .collect { searchDebounce.value = it }
        }
    }

    val searchResults: StateFlow<List<SearchResult>> = searchDebounce
        .flatMapLatest { query ->
            if (query.isBlank()) {
                flowOf(emptyList())
            } else {
                repository.searchPrefixFlow(query)
                    .catch { emit(emptyList()) }
            }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    private val _selectedWord = MutableStateFlow<String?>(null)
    val selectedWord: StateFlow<String?> = _selectedWord.asStateFlow()

    val selectedEntry: StateFlow<DictEntry?> = _selectedWord
        .flatMapLatest { word ->
            if (word.isNullOrBlank()) {
                flowOf(null)
            } else {
                repository.lookupFlow(word)
                    .catch { emit(null) }
            }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, null)

    fun onSearchQueryChange(query: String) {
        _searchQuery.value = query
    }

    fun onWordSelected(word: String) {
        _selectedWord.value = word
    }

    fun clearSelection() {
        _selectedWord.value = null
        _searchQuery.value = ""
    }

    class Factory(private val repository: DictRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return DictViewModel(repository) as T
        }
    }
}
