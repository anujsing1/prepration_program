package com.java2novoice;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

public class SortMapByValue {

	public static void main(String[] args) {
		Map<String, Integer> map = new HashMap<String, Integer>();
        map.put("java", 20);
        map.put("C++", 45);
        map.put("Java2Novice", 2);
        map.put("Unix", 67);
        map.put("MAC", 26);
        map.put("Why this kolavari", 93);
        printSortedMapByValue(map);
	}
	
	static void printSortedMapByValue(Map<String, Integer> map){
		Set<Entry<String, Integer>> set = map.entrySet();
		List<Entry<String,Integer>> list = new ArrayList<Entry<String,Integer>> (set);
//		List<Entry<String, Integer>> list = new ArrayList<Entry<String, Integer>>(set);
		Collections.sort(list, new Comparator<Map.Entry<String, Integer>>() {
			@Override
			public int compare(Entry<String, Integer> o1,
					Entry<String, Integer> o2) {
				return o1.getValue()-o2.getValue();
			}
		});
		
		for(Map.Entry<String, Integer> entry : list){
			System.out.println("Key : "+entry.getKey() + " - Value : "+entry.getValue());
		}
	}

}
