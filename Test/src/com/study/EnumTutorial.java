/**
 * 
 */
package com.study;

/**
 * @author govind.gupta
 *
 */
public class EnumTutorial {

	public enum DIRECTION {
		EAST(0), WEST(180), NORTH(90), SOUTH(270); // optionally can end with
													// ";"

		private Integer angel;

		public Integer getAngel() {
			return angel;
		}

		public void setAngel(Integer angel) {
			this.angel = angel;
		}

		private DIRECTION(Integer angel) {
			this.angel = angel;
		}

		public void shiftAngel(Integer degree) {
			this.angel += degree;
			if (this.angel >= 360) {
				this.angel -= 360;
			}
		}
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		DIRECTION[] directions = DIRECTION.values();
		for (DIRECTION direction : directions) {
			System.out.println("Direction is :- " + direction
					+ ", Name of direction is :- " + direction.name()
					+ ", Angel of the diction from EAST is :- "
					+ direction.angel + " & Order of direction is :- "
					+ direction.ordinal());
			direction.shiftAngel(180);
			// direction.setAngel(direction.getAngel() + 90);
			System.out.println(direction.getAngel());
		}
	}

}
